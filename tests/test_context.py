
import pytest

from backend.context import (
    INPUT_BUDGET,
    MessageTooLong,
    estimated_size,
    trim_history,
)


def test_short_conversation_is_preserved():
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]

    result = trim_history(history, "How are you?")

    assert len(result) == 3
    assert result[-1]["content"] == "How are you?"


def test_long_history_is_trimmed():
    history = [
        {"role": "user", "content": "old " * 400},
        {"role": "assistant", "content": "middle " * 100},
        {"role": "user", "content": "recent question"},
        {"role": "assistant", "content": "recent answer"},
    ]

    result = trim_history(history, "next question")

    assert result[-1]["content"] == "next question"
    assert "recent answer" in [m["content"] for m in result]
    assert "old " * 400 not in [m["content"] for m in result]
    assert sum(estimated_size(m) for m in result) <= INPUT_BUDGET


def test_single_oversized_message_is_rejected():
    with pytest.raises(MessageTooLong):
        trim_history([], "x" * 3000)


def test_history_is_not_modified():
    history = [{"role": "user", "content": "Hello"}]
    original = [message.copy() for message in history]

    trim_history(history, "New question")

    assert history == original


def test_zero_history():
    result = trim_history([], "Hello")

    assert result == [{"role": "user", "content": "Hello"}]
