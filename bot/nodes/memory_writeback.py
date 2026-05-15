"""
NODE-009: memory_writeback

Persists the current turn to Qdrant. Extracts new first-person persona facts
from the bot's final_response using regex. Returns only facts not already
in state["persona_facts"]. Failure is logged but does not block the response.
"""
import re
import logging
from bot.config import AppConfig
from bot.state import ConversationState
import bot.memory as memory_store

logger = logging.getLogger(__name__)

# Patterns for first-person self-claims by the bot
_FACT_PATTERNS = [
    r"\bI(?:'m| am)\s+([^.!?,]{3,60})",
    r"\bI prefer\s+([^.!?,]{3,60})",
    r"\bI like\s+([^.!?,]{3,60})",
    r"\bI love\s+([^.!?,]{3,60})",
    r"\bI hate\s+([^.!?,]{3,60})",
    r"\bI enjoy\s+([^.!?,]{3,60})",
    r"\bI don't like\s+([^.!?,]{3,60})",
    r"\bI can(?:'t| not)\s+([^.!?,]{3,60})",
    r"\bI always\s+([^.!?,]{3,60})",
    r"\bI never\s+([^.!?,]{3,60})",
]
_FACT_REGEX = re.compile("|".join(_FACT_PATTERNS), re.IGNORECASE)


def _extract_facts(text: str) -> list[str]:
    """Extract first-person claim snippets from bot response text."""
    facts = []
    for match in _FACT_REGEX.finditer(text):
        # Take the first non-None group
        snippet = next((g for g in match.groups() if g is not None), None)
        if snippet:
            fact = snippet.strip().rstrip(".,;")
            if 3 <= len(fact) <= 80:
                facts.append(fact)
    return facts


def make(config: AppConfig):
    """Factory that closes over config and returns the async node function."""

    async def run(state: ConversationState) -> dict:
        conversation_id = state.get("conversation_id", "")
        turn_index = state.get("turn_index", 0)
        final_response = state.get("final_response", "")
        normalized_message = state.get("normalized_message", "")
        existing_facts: list[str] = state.get("persona_facts") or []

        # Persist turn to Qdrant
        try:
            client = memory_store.get_client(config.memory.qdrant_path)
            if normalized_message and final_response:
                memory_store.store_turn(
                    client=client,
                    conversation_id=conversation_id,
                    turn=turn_index,
                    user_msg=normalized_message,
                    bot_response=final_response,
                )
        except Exception as e:
            logger.warning("NODE-009 Qdrant writeback failed: %s", e)

        # Extract new persona facts
        new_facts: list[str] = []
        if final_response:
            try:
                extracted = _extract_facts(final_response)
                # Only keep facts not already known
                existing_set = set(f.lower() for f in existing_facts)
                new_facts = [f for f in extracted if f.lower() not in existing_set]
                if new_facts:
                    logger.debug("NODE-009 new persona facts: %s", new_facts)
            except Exception as e:
                logger.warning("NODE-009 fact extraction failed: %s", e)

        return {
            "persona_facts": new_facts,  # reducer will append
        }

    return run
