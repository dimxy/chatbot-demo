"""
NODE-001: input_receiver

Validates and normalizes the raw user message, appends a HumanMessage to
conversation history, increments turn_index, and stamps last_updated.
"""
import logging
import time
from langchain_core.messages import HumanMessage
from bot.state import ConversationState

logger = logging.getLogger(__name__)


async def run(state: ConversationState) -> dict:
    raw = state.get("raw_user_message", "")

    # Coerce to string if needed
    if not isinstance(raw, str):
        raw = str(raw)

    normalized = raw.strip()

    if not normalized:
        raise ValueError("Empty message received. Please enter a non-empty message.")

    turn_index = state.get("turn_index", 0) + 1
    logger.debug("NODE-001 turn=%d message=%r", turn_index, normalized[:80])

    return {
        "normalized_message": normalized,
        "messages": [HumanMessage(content=normalized)],
        "turn_index": turn_index,
        "last_updated": time.time(),
    }
