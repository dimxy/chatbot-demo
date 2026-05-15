"""
NODE-004: emotional_state_update

Applies emotional state updates in the required order:
  1. Decay toward personality baseline
  2. Apply stimulus deltas scaled by volatility
  3. Clamp to valid ranges
  4. Detect and log trigger events (delta > 0.4 on any dimension)

Also implements EMO-005: if valence < -0.7 for 5+ consecutive turns,
temporarily double decay_rate until valence recovers above -0.5.
"""
import logging
import time
from dataclasses import replace
from bot.state import ConversationState, EmotionalState, TriggerEvent

logger = logging.getLogger(__name__)

_TRIGGER_THRESHOLD = 0.4
_NEGATIVE_FLOOR_THRESHOLD = -0.7
_NEGATIVE_RECOVERY_THRESHOLD = -0.5
_MAX_CONSECUTIVE_NEGATIVE = 5


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


async def run(state: ConversationState) -> dict:
    mood: EmotionalState = state.get("bot_mood") or EmotionalState()
    personality = state.get("personality")
    impact = state.get("impact_estimate") or {}
    turn_index = state.get("turn_index", 1)
    consecutive_neg = state.get("consecutive_negative_turns", 0)

    # EMO-005: temporarily double decay_rate when stuck negative
    effective_decay = personality.decay_rate
    if consecutive_neg >= _MAX_CONSECUTIVE_NEGATIVE:
        effective_decay = min(1.0, personality.decay_rate * 2.0)
        logger.debug(
            "NODE-004 EMO-005 doubling decay_rate %.2f -> %.2f (neg_turns=%d)",
            personality.decay_rate, effective_decay, consecutive_neg,
        )

    # --- Step 1: Decay toward baseline (one turn elapsed) ---
    decay_factor = 1.0 - effective_decay  # turns_elapsed = 1
    v_decayed = personality.baseline_valence + (mood.valence - personality.baseline_valence) * decay_factor
    a_decayed = personality.baseline_arousal + (mood.arousal - personality.baseline_arousal) * decay_factor
    d_decayed = personality.baseline_dominance + (mood.dominance - personality.baseline_dominance) * decay_factor

    # --- Step 2: Apply stimulus deltas scaled by volatility ---
    vol = personality.emotional_volatility
    v_new = v_decayed + impact.get("valence", 0.0) * vol
    a_new = a_decayed + impact.get("arousal", 0.0) * vol
    d_new = d_decayed + impact.get("dominance", 0.0) * vol

    # --- Step 3: Clamp ---
    v_clamped = _clamp(v_new, -1.0, 1.0)
    a_clamped = _clamp(a_new, 0.0, 1.0)
    d_clamped = _clamp(d_new, -1.0, 1.0)

    new_mood = EmotionalState(
        valence=v_clamped,
        arousal=a_clamped,
        dominance=d_clamped,
        last_updated=time.time(),
    )

    # --- Step 4: Trigger detection ---
    new_events: list[TriggerEvent] = []
    deltas = {
        "valence": v_clamped - mood.valence,
        "arousal": a_clamped - mood.arousal,
        "dominance": d_clamped - mood.dominance,
    }
    triggered_dims = {k: v for k, v in deltas.items() if abs(v) > _TRIGGER_THRESHOLD}
    if triggered_dims:
        raw_msg = state.get("normalized_message", "")
        trigger_text = raw_msg[:200]
        category = _categorize_trigger(state.get("user_intent", "other"), triggered_dims)
        event = TriggerEvent(
            turn=turn_index,
            timestamp=time.time(),
            trigger_text=trigger_text,
            shift=triggered_dims,
            category=category,
        )
        new_events.append(event)
        logger.debug("NODE-004 trigger event: %s dims=%s", category, triggered_dims)

    # EMO-005: update consecutive negative counter
    if v_clamped < _NEGATIVE_FLOOR_THRESHOLD:
        new_consecutive_neg = consecutive_neg + 1
    elif v_clamped >= _NEGATIVE_RECOVERY_THRESHOLD:
        new_consecutive_neg = 0
    else:
        new_consecutive_neg = consecutive_neg

    logger.debug(
        "NODE-004 mood v=%.3f a=%.3f d=%.3f (was v=%.3f a=%.3f d=%.3f)",
        v_clamped, a_clamped, d_clamped,
        mood.valence, mood.arousal, mood.dominance,
    )

    return {
        "bot_mood": new_mood,
        "emotional_events": new_events,
        "consecutive_negative_turns": new_consecutive_neg,
    }


def _categorize_trigger(intent: str, dims: dict) -> str:
    """Heuristically categorize a trigger event from intent and deltas."""
    v_delta = dims.get("valence", 0.0)
    if intent == "confrontation" and v_delta < 0:
        return "insult"
    if intent == "vent":
        return "confusion"
    if v_delta > 0.4:
        return "praise"
    if v_delta < -0.4:
        return "insult"
    if dims.get("arousal", 0.0) > 0.4:
        return "surprise"
    return "other"
