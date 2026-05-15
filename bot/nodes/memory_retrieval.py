"""
NODE-002: context_memory_retrieval

Loads short-term buffer from state messages, retrieves relevant long-term
memories from Qdrant, and surfaces persona facts and emotional events.
"""
import logging
from bot.config import AppConfig
from bot.state import ConversationState
import bot.memory as memory_store

logger = logging.getLogger(__name__)


def make(config: AppConfig):
    """Factory that closes over config and returns the async node function."""

    async def run(state: ConversationState) -> dict:
        query = state.get("normalized_message", "")
        messages = state.get("messages", [])
        conversation_id = state.get("conversation_id", "")

        # Short-term window from message history
        recent_history = memory_store.get_short_term(
            messages, limit=config.memory.short_term_turns
        )

        # Long-term retrieval from Qdrant
        long_term_facts: list[str] = []
        if query:
            try:
                client = memory_store.get_client(config.memory.qdrant_path)
                long_term_facts = memory_store.retrieve_relevant(
                    client, query, top_k=config.memory.long_term_top_k
                )
            except Exception as e:
                logger.warning("NODE-002 long-term retrieval failed: %s", e)

        logger.debug(
            "NODE-002 short_term=%d long_term=%d",
            len(recent_history),
            len(long_term_facts),
        )

        return {
            "recent_history": recent_history,
            "long_term_facts": long_term_facts,
        }

    return run
