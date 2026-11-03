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


def test_prompt_library_filters_and_prefills_without_submitting():
    def request(method, url, **kwargs):
        return Response({'models': ['qwen2.5:1.5b']} if url.endswith('/models') else [])

    with patch('requests.request', side_effect=request), patch('requests.post') as generate:
        dashboard = AppTest.from_file(str(APP)).run()
        dashboard.radio(key='workspace_view').set_value('Prompt library').run()
        assert not dashboard.exception
        dashboard.radio(key='prompt_category').set_value('Code').run()
        prompt_buttons = [button for button in dashboard.button if button.label == 'Use prompt']
        assert len(prompt_buttons) == 2
        dashboard.button(key='use_library_debug').click().run()
        assert not dashboard.exception
        assert dashboard.session_state['workspace_view'] == 'Chat'
        assert dashboard.session_state['conversation_id'] is None
        assert 'Help me debug a problem' in dashboard.chat_input[0].proto.value
        generate.assert_not_called()


def test_history_search_reopen_and_new_chat():
    identifier = '00000000-0000-0000-0000-000000000001'
    conversation = {'id': identifier, 'title': 'Release plan', 'messages': [
        {'role': 'user', 'content': 'Plan a release'},
        {'role': 'assistant', 'content': 'Start with a checklist.', 'model': 'qwen2.5:1.5b'}]}

    def request(method, url, **kwargs):
        if url.endswith('/models'):
            return Response({'models': ['qwen2.5:1.5b']})
        return Response([conversation] if url.endswith('/conversations') else conversation)

    with patch('requests.request', side_effect=request):
        dashboard = AppTest.from_file(str(APP)).run()
        dashboard.radio(key='workspace_view').set_value('History').run()
        assert not dashboard.exception
        dashboard.text_input(key='history_search').set_value('missing').run()
        assert 'No matching chats' in dashboard.info[0].value
        dashboard.text_input(key='history_search').set_value('RELEASE').run()
        dashboard.button(key=f'open_{identifier}').click().run()
        assert not dashboard.exception
        assert len(dashboard.chat_message) == 2
        assert dashboard.query_params['chat'] == identifier
        assert {button.label for button in dashboard.get('download_button')} == {
            'Download Markdown', 'Download JSON'}
        dashboard.button(key='new_chat').click().run()
        assert not dashboard.exception
        assert len(dashboard.chat_message) == 0
        assert dashboard.session_state['conversation_id'] is None
        assert 'chat' not in dashboard.query_params


def test_history_requires_confirmation_and_handles_delete():
    identifier = '00000000-0000-0000-0000-000000000001'
    saved = [{'id': identifier, 'title': 'Disposable test chat'}]

    def request(method, url, **kwargs):
        if method == 'DELETE':
            saved.clear()
            return Response({'deleted': True})
        if url.endswith('/models'):
            return Response({'models': []})
        return Response(saved)

    with patch('requests.request', side_effect=request) as mocked:
        dashboard = AppTest.from_file(str(APP)).run()
        dashboard.radio(key='workspace_view').set_value('History').run()
        dashboard.button(key=f'delete_{identifier}').click().run()
        assert not any(call.args[0] == 'DELETE' for call in mocked.call_args_list)
        dashboard.button(key=f'cancel_{identifier}').click().run()
        assert dashboard.session_state['pending_delete'] is None
        assert len(saved) == 1
        dashboard.button(key=f'delete_{identifier}').click().run()
        dashboard.button(key=f'confirm_{identifier}').click().run()
        assert not dashboard.exception
        assert not saved
        assert dashboard.session_state['pending_delete'] is None


def test_model_preferences_survive_navigation_and_prompt_selection():
    def request(method, url, **kwargs):
        return Response({'models': ['qwen2.5:1.5b', 'other:latest']} if url.endswith('/models') else [])

    with patch('requests.request', side_effect=request):
        dashboard = AppTest.from_file(str(APP)).run()
        dashboard.selectbox(key='selected_model').set_value('other:latest').run()
        dashboard.slider(key='memory').set_value(20).run()
        dashboard.radio(key='workspace_view').set_value('Prompt library').run()
        dashboard.button(key='use_library_project').click().run()
        assert not dashboard.exception
        assert dashboard.selectbox(key='selected_model').value == 'other:latest'
        assert dashboard.slider(key='memory').value == 20
