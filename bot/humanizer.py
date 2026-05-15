import re
import random
from typing import Optional
from bot.state import EmotionalState, Personality

FILLERS = ["um,", "uh,", "like,", "you know,"]
HEDGES = ["I think", "maybe", "kind of", "sort of", "I guess"]


def humanize(
    text: str,
    mood: EmotionalState,
    personality: Personality,
    intensity: float = 1.0,
    seed: Optional[int] = None,
) -> str:
    """
    Post-process text to inject human-like disfluencies based on mood and personality.

    Pure text manipulation — no LLM calls.
    At expressiveness=0 or intensity=0, returns text unchanged.
    Accepts optional seed for deterministic output (useful in tests).
    """
    if personality.expressiveness < 0.01 or intensity < 0.01:
        return text

    rng = random.Random(seed)
    expr = personality.expressiveness * intensity

    # Split on sentence-ending punctuation, preserving it
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    result = []

    for i, sentence in enumerate(parts):
        if not sentence:
            continue

        # Filler prefix (high arousal) — only for sentences after the first
        if i > 0 and rng.random() < expr * mood.arousal * 0.35:
            filler = rng.choice(FILLERS)
            sentence = filler + " " + sentence[0].lower() + sentence[1:]

        # Hedge prefix (low dominance)
        if rng.random() < expr * max(0.0, -mood.dominance) * 0.4:
            hedge = rng.choice(HEDGES)
            sentence = hedge + " " + sentence[0].lower() + sentence[1:]

        # Trailing ellipsis (low valence)
        if rng.random() < expr * max(0.0, -mood.valence) * 0.35:
            sentence = re.sub(r"[.!?]+$", "", sentence) + "..."

        # Trailing exclamation (high arousal + positive valence)
        elif mood.arousal > 0.6 and mood.valence > 0.3 and rng.random() < expr * 0.2:
            sentence = re.sub(r"\.+$", "!", sentence)

        result.append(sentence)

    return " ".join(result)
