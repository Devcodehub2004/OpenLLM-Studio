"""Local FastAPI service, Ollama streaming, and durable conversation memory."""
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from backend.store import Store

MODEL = 'qwen2.5:1.5b'
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
OLLAMA_URL = f'{OLLAMA_BASE_URL}/api/chat'


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=16000)
    conversation_id: UUID | None = None
    model: str = Field(default=MODEL, min_length=1, max_length=200)
    temperature: float = Field(default=0.7, ge=0, le=2, allow_inf_nan=False)
    memory_turns: int = Field(default=10, ge=0, le=50)

    @field_validator('message', 'model')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Must not be blank')
        return value.strip()


class ConversationRequest(BaseModel):
    title: str = Field(default='New conversation', min_length=1, max_length=80)

    @field_validator('title')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Title must not be blank')
        return value.strip()


@asynccontextmanager
async def lifespan(app):
    app.state.store = Store(os.getenv('OPENLLM_DB_PATH', str(
        Path(__file__).resolve().parents[1] / 'data' / 'chat.db')))
    app.state.busy = set()
    async with httpx.AsyncClient(timeout=httpx.Timeout(180, connect=5)) as client:
        app.state.ollama = client
        yield


app = FastAPI(title='OpenLLM Studio API', lifespan=lifespan)


@app.exception_handler(sqlite3.Error)
async def database_error(request, exc):
    return JSONResponse(status_code=503, content={'detail': 'Chat storage is unavailable. Please retry.'})


@app.get('/')
def home():
    return {'status': 'OpenLLM Studio is running'}


async def installed_models():
    try:
        response = await app.state.ollama.get(f'{OLLAMA_BASE_URL}/api/tags')
        response.raise_for_status()
        return sorted({m['name'] for m in response.json()['models']
                       if isinstance(m['name'], str)})
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise HTTPException(503, 'Ollama is unavailable. Start Ollama and refresh models.') from None


@app.get('/models')
async def models():
    return {'models': await installed_models()}


@app.get('/conversations')
def conversations():
    return app.state.store.list()


@app.post('/conversations', status_code=201)
def create_conversation(body: ConversationRequest):
    return app.state.store.create(body.title)


@app.get('/conversations/{identifier}')
def get_conversation(identifier: UUID):
    try:
        return app.state.store.get(str(identifier))
    except KeyError:
        raise HTTPException(404, 'Conversation not found') from None


@app.delete('/conversations/{identifier}')
async def delete_conversation(identifier: UUID):
    identifier = str(identifier)
    if identifier in app.state.busy:
        raise HTTPException(409, 'Wait for this conversation to finish generating.')
    if not app.state.store.delete(identifier):
        raise HTTPException(404, 'Conversation not found')
    return {'deleted': True}


async def prepare(body):
    if body.model not in await installed_models():
        raise HTTPException(422, 'Select an installed Ollama model. Refresh the model list.')
    if body.conversation_id:
        conversation = get_conversation(body.conversation_id)
    else:
        conversation = app.state.store.create()
    identifier = conversation['id']
    if identifier in app.state.busy:
        raise HTTPException(409, 'This conversation is already generating a reply.')
    app.state.busy.add(identifier)
    history = conversation['messages'][-2 * body.memory_turns:] if body.memory_turns else []
    messages = [{'role': m['role'], 'content': m['content']} for m in history]
    messages.append({'role': 'user', 'content': body.message})
    return identifier, {'model': body.model, 'messages': messages,
                        'options': {'temperature': body.temperature}}


def event(kind, **data):
    return json.dumps({'type': kind, **data}, ensure_ascii=False) + '\n'


async def tokens(payload):
    async with app.state.ollama.stream('POST', OLLAMA_URL, json={**payload, 'stream': True}) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line:
                continue
            item = json.loads(line)
            if not isinstance(item, dict) or not isinstance(item.get('message', {}), dict):
                raise TypeError('Invalid model response')
            if item.get('error'):
                raise ValueError('Ollama returned an error')
            content = item.get('message', {}).get('content', '')
            if not isinstance(content, str):
                raise TypeError('Invalid model response')
            if content:
                yield content
            if item.get('done') is True:
                return
        raise ValueError('Ollama stream ended before completion')


@app.post('/chat')
async def chat(body: ChatRequest):
    identifier, payload = await prepare(body)
    try:
        response = await app.state.ollama.post(OLLAMA_URL, json={**payload, 'stream': False})
        response.raise_for_status()
        item = response.json()
        answer = item['message']['content']
        if item.get('error') or not isinstance(answer, str) or not answer.strip():
            raise ValueError('Empty or invalid reply')
        app.state.store.save_turn(identifier, body.message, answer, body.model)
        return {'reply': answer, 'conversation_id': identifier, 'model': body.model}
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise HTTPException(503, 'AI model is unavailable or returned an invalid reply. Please retry.') from None
    finally:
        app.state.busy.discard(identifier)


@app.post('/chat/stream')
async def stream_chat(body: ChatRequest, request: Request):
    identifier, payload = await prepare(body)

    async def generate():
        try:
            yield event('start', conversation_id=identifier, model=body.model)
            chunks = []
            async for chunk in tokens(payload):
                if await request.is_disconnected():
                    return
                chunks.append(chunk)
                yield event('delta', content=chunk)
            answer = ''.join(chunks)
            if not answer.strip():
                raise ValueError('Empty reply')
            if await request.is_disconnected():
                return
            app.state.store.save_turn(identifier, body.message, answer, body.model)
            yield event('done', conversation_id=identifier)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, sqlite3.Error):
            yield event('error', message='Reply could not be completed or saved. Please retry; this turn was not saved.')
        finally:
            app.state.busy.discard(identifier)

    return StreamingResponse(generate(), media_type='application/x-ndjson',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
