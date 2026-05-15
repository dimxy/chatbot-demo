"""
NODE-003: intent_mood_analyzer

Makes a lightweight LLM call to classify user intent, detect sentiment,
and propose mood dimension deltas. Uses a plain JSON prompt for broad
compatibility with Ollama models. Falls back to neutral values on failure.
"""
import json
import logging
from bot.config import AppConfig
from bot.llm import get_llm
from bot.state import ConversationState

logger = logging.getLogger(__name__)

_INTENT_ENUM = ["question", "vent", "joke", "confrontation", "request", "smalltalk", "other"]

_SYSTEM_PROMPT = """You are an intent and sentiment classifier. Given a user message, output ONLY a valid JSON object with these exact keys:
- "intent": one of ["question", "vent", "joke", "confrontation", "request", "smalltalk", "other"]
- "user_sentiment": a float between -1.0 (very negative) and 1.0 (very positive)
- "impact_estimate": an object with keys "valence", "arousal", "dominance", each a float delta (e.g. 0.1, -0.2)

Output only the raw JSON, no explanation, no markdown, no code fences."""


def make(config: AppConfig):
    """Factory that closes over config and returns the async node function."""

    async def run(state: ConversationState) -> dict:
        message = state.get("normalized_message", "")
        recent_history = state.get("recent_history", [])

        # Build context from recent history (last few exchanges)
        context_lines = []
        for msg in recent_history[-6:]:
            if hasattr(msg, "type"):
                role = "User" if msg.type == "human" else "Bot"
                context_lines.append(f"{role}: {msg.content}")
            elif hasattr(msg, "content"):
                context_lines.append(str(msg.content))

        context = "\n".join(context_lines)
        user_prompt = f"Context:\n{context}\n\nLatest message: {message}" if context else message

        try:
            llm = get_llm(config, model_key="intent_analyzer")
            from langchain_core.messages import SystemMessage, HumanMessage
            response = await llm.ainvoke([
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            raw = response.content.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(
                    line for line in lines
                    if not line.startswith("```")
                )

            parsed = json.loads(raw)

            intent = parsed.get("intent", "other")
            if intent not in _INTENT_ENUM:
                intent = "other"

            user_sentiment = float(parsed.get("user_sentiment", 0.0))
            user_sentiment = max(-1.0, min(1.0, user_sentiment))

            impact_raw = parsed.get("impact_estimate", {})
            impact_estimate = {
                "valence": float(impact_raw.get("valence", 0.0)),
                "arousal": float(impact_raw.get("arousal", 0.0)),
                "dominance": float(impact_raw.get("dominance", 0.0)),
            }

            logger.debug(
                "NODE-003 intent=%s sentiment=%.2f impact=%s",
                intent, user_sentiment, impact_estimate,
            )

        except Exception as e:
            logger.warning("NODE-003 LLM call failed: %s — using neutral fallback", e)
            intent = "other"
            user_sentiment = 0.0
            impact_estimate = {"valence": 0.0, "arousal": 0.0, "dominance": 0.0}

        return {
            "user_intent": intent,
            "user_sentiment": user_sentiment,
            "impact_estimate": impact_estimate,
        }

    return run
