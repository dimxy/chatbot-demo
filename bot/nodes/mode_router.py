"""
NODE-005: response_mode_router

Pure function. Reads bot_mood, user_intent, topic_state from state and
selects a response mode key from MODE_REGISTRY. No LLM call, no side effects.

Rules (MODE-003):
  - user_intent == 'vent' or user_sentiment < -0.5  → emotional
  - bot_mood.valence > 0.5 and bot_mood.arousal > 0.5 and user_intent == 'joke' → playful
  - topic_state.confidence < 0.4                    → uncertain
  - topic_state.confidence > 0.7                    → confident
  - else                                             → default
"""
import logging
from bot.modes import MODE_REGISTRY, DEFAULT_MODE
from bot.state import ConversationState

logger = logging.getLogger(__name__)


async def run(state: ConversationState) -> dict:
    mood = state.get("bot_mood")
    user_intent = state.get("user_intent", "other")
    user_sentiment = state.get("user_sentiment", 0.0)
    topic_state = state.get("topic_state")

    valence = mood.valence if mood else 0.0
    arousal = mood.arousal if mood else 0.3
    confidence = topic_state.confidence if topic_state else 0.5

    # Apply routing rules in priority order
    if user_intent == "vent" or user_sentiment < -0.5:
        mode = "emotional"
    elif valence > 0.5 and arousal > 0.5 and user_intent == "joke":
        mode = "playful"
    elif confidence < 0.4:
        mode = "uncertain"
    elif confidence > 0.7:
        mode = "confident"
    else:
        mode = DEFAULT_MODE

    # Safety check: ensure mode is registered
    if mode not in MODE_REGISTRY:
        logger.warning("NODE-005 unknown mode %r, falling back to default", mode)
        mode = DEFAULT_MODE

    logger.debug("NODE-005 mode=%s (intent=%s sentiment=%.2f conf=%.2f)", mode, user_intent, user_sentiment, confidence)

    return {"response_mode": mode}
