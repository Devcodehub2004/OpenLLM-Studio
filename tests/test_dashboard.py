from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'frontend' / 'app.py'


class Response:
    ok = True

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def iter_lines(self, **kwargs):
        import json
        return iter(json.dumps(item).encode() for item in self.data)


def test_dashboard_ready_and_empty_models():
    for models in [['qwen2.5:1.5b', 'other:latest'], []]:
        def request(method, url, models=models, **kwargs):
            return Response({'models': models} if url.endswith('/models') else [])
        with patch('requests.request', side_effect=request):
            dashboard = AppTest.from_file(str(APP)).run()
            assert not dashboard.exception
            assert any(
    "How can I help you today?" in item.value
    for item in dashboard.markdown
)
            assert dashboard.chat_input[0].disabled == (not models)


def test_dashboard_backend_unavailable():
    import requests
    with patch('requests.request', side_effect=requests.ConnectionError('offline')):
        dashboard = AppTest.from_file(str(APP)).run()
        assert not dashboard.exception
        assert 'Cannot load saved chats' in dashboard.error[0].value


def test_dashboard_streaming_and_reopened_history():
    identifier = '00000000-0000-0000-0000-000000000001'
    conversation = {'id': identifier, 'title': 'Hello', 'messages': []}
    state = {'saved': False}

    def request(method, url, **kwargs):
        if url.endswith('/models'):
            return Response({'models': ['qwen2.5:1.5b']})
        if url.endswith('/conversations'):
            return Response([conversation] if state['saved'] else [])
        return Response(conversation)

    def post(url, **kwargs):
        state['saved'] = True
        conversation['messages'] = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi Ada', 'model': 'qwen2.5:1.5b', 'created_at': 'now'}]
        return Response([{'type': 'start', 'conversation_id': identifier},
                         {'type': 'delta', 'content': 'Hi Ada'}, {'type': 'done'}])

    with patch('requests.request', side_effect=request), patch('requests.post', side_effect=post):
        dashboard = AppTest.from_file(str(APP)).run()
        dashboard.chat_input[0].set_value('Hello').run()
        assert not dashboard.exception
        assert len(dashboard.chat_message) == 2
        assert dashboard.session_state['conversation_id'] == identifier
        assert dashboard.session_state['retry_prompt'] is None


def test_dashboard_partial_stream_failure():
    def request(method, url, **kwargs):
        if url.endswith('/models'):
            return Response({'models': ['qwen2.5:1.5b']})
        return Response([])

    with patch('requests.request', side_effect=request), patch('requests.post', return_value=Response([
            {'type': 'delta', 'content': 'Partial'}, {'type': 'error', 'message': 'Model interrupted'}])):
        dashboard = AppTest.from_file(str(APP)).run()
        dashboard.chat_input[0].set_value('Hello').run()
        assert not dashboard.exception
        assert 'Model interrupted' in dashboard.error[0].value
        assert dashboard.session_state['retry_prompt'] == 'Hello'
