import asyncio
from typing import AsyncGenerator
from bot.state import EmotionalState

_WORDS_PER_CHUNK = 12


async def pace_response(
    text: str,
    mood: EmotionalState,
    enabled: bool = True,
    max_delay: float = 4.0,
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields text chunks with mood-driven delays.

    When disabled, yields the full text immediately.
    Delay formula: (1.0 - arousal) * 1.5 + 0.3, capped at max_delay.
    High arousal → faster delivery; low arousal → slower, more contemplative.
    """
    if not enabled:
        yield text
        return

    words = text.split()
    chunks = [
        " ".join(words[i : i + _WORDS_PER_CHUNK])
        for i in range(0, len(words), _WORDS_PER_CHUNK)
    ] or [text]

    for chunk in chunks:
        yield chunk
        if len(chunks) > 1:
            delay = min((1.0 - mood.arousal) * 1.5 + 0.3, max_delay)
            await asyncio.sleep(delay)
