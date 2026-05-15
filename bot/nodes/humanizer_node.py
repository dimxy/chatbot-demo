"""
NODE-007: humanizer

Wraps bot/humanizer.py to post-process draft_response with disfluencies,
hedges, and emotional artifacts. Reads intensity from config.

At expressiveness=0 or intensity=0, output is unchanged.
Falls back to draft_response on any exception.
"""
import logging
from bot.config import AppConfig
from bot.humanizer import humanize
from bot.state import ConversationState

logger = logging.getLogger(__name__)


def make(config: AppConfig):
    """Factory that closes over config and returns the async node function."""

    async def run(state: ConversationState) -> dict:
        draft = state.get("draft_response", "")
        mood = state.get("bot_mood")
        personality = state.get("personality")
        intensity = config.humanizer.intensity

        if not draft:
            return {"final_response": draft}

        try:
            final = humanize(
                text=draft,
                mood=mood,
                personality=personality,
                intensity=intensity,
            )
        except Exception as e:
            logger.warning("NODE-007 humanizer failed: %s — using draft unchanged", e)
            final = draft

        logger.debug("NODE-007 intensity=%.2f draft_len=%d final_len=%d", intensity, len(draft), len(final))

        return {"final_response": final}

    return run
