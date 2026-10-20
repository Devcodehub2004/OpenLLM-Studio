import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.store import Store


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setenv('OPENLLM_DB_PATH', str(tmp_path / 'chat.db'))
    calls = []
    mode = {'value': 'ok'}

    def handle(request):
        if mode['value'] == 'offline':
            raise httpx.ConnectError('offline', request=request)
        if request.url.path == '/api/tags':
            return httpx.Response(200, json={'models': [
                {'name': 'qwen2.5:1.5b'}, {'name': 'other:latest'}]})
        payload = json.loads(request.content)
        calls.append(payload)
        if payload['stream']:
            lines = [{'message': {'content': 'Hello '}}, {'message': {'content': 'world'}}]
            if mode['value'] == 'ok':
                lines.append({'done': True})
            elif mode['value'] == 'error':
                lines.append({'error': 'model failed'})
            elif mode['value'] == 'malformed':
                return httpx.Response(200, text='not json\n')
            return httpx.Response(200, text=''.join(json.dumps(line) + '\n' for line in lines))
        return httpx.Response(200, json={'message': {'content': 'Hello world'}, 'done': True})

    with TestClient(app) as client:
        original = app.state.ollama
        mocked = httpx.AsyncClient(transport=httpx.MockTransport(handle))
        app.state.ollama = mocked
        yield client, calls, mode, tmp_path / 'chat.db'
        client.portal.call(mocked.aclose)
        app.state.ollama = original


def new(client):
    response = client.post('/conversations', json={})
    assert response.status_code == 201
    return response.json()['id']


def test_legacy_chat_and_memory_isolation(service):
    client, calls, _, path = service
    assert client.get('/').json() == {'status': 'OpenLLM Studio is running'}
    first = client.post('/chat', json={'message': 'My name is Ada'}).json()
    assert first['reply'] == 'Hello world'
    identifier = first['conversation_id']
    response = client.post('/chat', json={'message': 'My name?', 'conversation_id': identifier,
                                        'model': 'other:latest'})
    assert response.status_code == 200
    assert calls[-1]['model'] == 'other:latest'
    assert [m['role'] for m in calls[-1]['messages']] == ['user', 'assistant', 'user']
    assert calls[-1]['messages'][0]['content'] == 'My name is Ada'
    second = new(client)
    client.post('/chat', json={'message': 'Separate', 'conversation_id': second})
    assert len(calls[-1]['messages']) == 1
    # Reopening SQLite simulates restart, without an in-memory history cache.
    reopened = Store(path)
    assert len(reopened.get(identifier)['messages']) == 4
    assert reopened.get(identifier)['messages'][-1]['model'] == 'other:latest'
    assert reopened.get(identifier)['title'] == 'My name is Ada'


def test_stream_protocol_and_persistence(service):
    client, _, _, _ = service
    identifier = new(client)
    response = client.post('/chat/stream', json={'message': 'Hi', 'conversation_id': identifier})
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/x-ndjson')
    events = [json.loads(line) for line in response.iter_lines()]
    assert [e['type'] for e in events] == ['start', 'delta', 'delta', 'done']
    assert ''.join(e['content'] for e in events if e['type'] == 'delta') == 'Hello world'
    assert client.get(f'/conversations/{identifier}').json()['messages'][-1]['content'] == 'Hello world'
    assert not app.state.busy


@pytest.mark.parametrize('failure', ['truncated', 'error', 'malformed'])
def test_failed_stream_never_saves_partial_turn(service, failure):
    client, _, mode, _ = service
    identifier = new(client)
    mode['value'] = failure
    response = client.post('/chat/stream', json={'message': 'Hi', 'conversation_id': identifier})
    events = [json.loads(line) for line in response.iter_lines()]
    assert events[-1]['type'] == 'error'
    assert not client.get(f'/conversations/{identifier}').json()['messages']
    assert not app.state.busy


def test_memory_limit_and_zero(service):
    client, calls, _, _ = service
    identifier = new(client)
    for prompt in ['one', 'two', 'three']:
        client.post('/chat', json={'message': prompt, 'conversation_id': identifier})
    client.post('/chat', json={'message': 'four', 'conversation_id': identifier, 'memory_turns': 1})
    assert len(calls[-1]['messages']) == 3
    assert calls[-1]['messages'][0]['content'] == 'three'
    client.post('/chat', json={'message': 'five', 'conversation_id': identifier, 'memory_turns': 0})
    assert len(calls[-1]['messages']) == 1


@pytest.mark.parametrize('changes', [
    {'message': ''}, {'message': '  '}, {'message': 'x' * 16001},
    {'temperature': -1}, {'temperature': 3}, {'memory_turns': -1}, {'memory_turns': 51},
    {'model': 'not-installed'}, {'conversation_id': 'invalid'},
])
def test_validation(service, changes):
    client, calls, _, _ = service
    response = client.post('/chat', json={'message': 'Hi', **changes})
    assert response.status_code == 422
    assert not calls


def test_offline_and_missing_conversation(service):
    client, _, mode, _ = service
    assert len(client.get('/models').json()['models']) == 2
    missing = '00000000-0000-0000-0000-000000000000'
    assert client.get(f'/conversations/{missing}').status_code == 404
    assert client.post('/chat', json={'message': 'Hi', 'conversation_id': missing}).status_code == 404
    mode['value'] = 'offline'
    assert client.get('/models').status_code == 503
    assert client.post('/chat', json={'message': 'Hi'}).status_code == 503


def test_delete_cascade_and_busy_guard(service):
    client, _, _, path = service
    identifier = new(client)
    client.post('/chat', json={'message': "SQL ' quote", 'conversation_id': identifier})
    app.state.busy.add(identifier)
    assert client.delete(f'/conversations/{identifier}').status_code == 409
    assert client.post('/chat', json={'message': 'Other', 'conversation_id': identifier}).status_code == 409
    app.state.busy.clear()
    assert client.delete(f'/conversations/{identifier}').status_code == 200
    with Store(path).connection() as db:
        assert db.execute('SELECT count(*) FROM messages').fetchone()[0] == 0
    assert client.delete(f'/conversations/{identifier}').status_code == 404
