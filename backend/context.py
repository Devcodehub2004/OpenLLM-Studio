
"""Conservative context budgeting for local Ollama models."""

CONTEXT_WINDOW = 4096
RESPONSE_TOKENS = 1024
INPUT_BUDGET = 2500
MESSAGE_OVERHEAD = 32


class MessageTooLong(ValueError):
    """A single user message exceeds our input budget."""


def estimated_size(message: dict) -> int:
    """Conservative byte-based estimate, not an exact token count."""
    text = message["content"]
    return len(text.encode("utf-8")) + MESSAGE_OVERHEAD


def trim_history(history: list[dict], user_message: str) -> list[dict]:
    current = {"role": "user", "content": user_message}

    used = estimated_size(current)
    if used > INPUT_BUDGET:
        raise MessageTooLong(
            "Message is too long for the configured context budget."
        )

    selected = []

    # Work backwards, keeping the most recent history that fits.
    for message in reversed(history):
        size = estimated_size(message)

        if used + size > INPUT_BUDGET:
            break

        selected.append({
            "role": message["role"],
            "content": message["content"],
        })
        used += size

    selected.reverse()

    return selected + [current]
