import time
import operator
from dataclasses import dataclass, field
from typing import TypedDict, Annotated, Optional


@dataclass
class EmotionalState:
    valence: float = 0.0
    arousal: float = 0.3
    dominance: float = 0.0
    last_updated: float = field(default_factory=time.time)


@dataclass
class Personality:
    baseline_valence: float = 0.1
    baseline_arousal: float = 0.3
    baseline_dominance: float = 0.0
    emotional_volatility: float = 0.5
    decay_rate: float = 0.2
    expressiveness: float = 0.6


@dataclass
class TopicState:
    topic: str = ""
    confidence: float = 0.5
    engagement: float = 0.5


@dataclass
class TriggerEvent:
    turn: int
    timestamp: float
    trigger_text: str
    shift: dict
    category: str


@dataclass
class PersonaConfig:
    name: str
    gender: str
    emotional_distance: float = 0.5
    warmth: float = 0.6
    sexuality: str = "distracted"
    playfulness: float = 0.5


class ConversationState(TypedDict, total=False):
    # input fields set by CLI each turn
    raw_user_message: str
    conversation_id: str
    # per-turn computed fields
    normalized_message: str
    user_intent: str
    user_sentiment: float
    impact_estimate: dict
    detected_language: str
    detected_script: str
    response_mode: str
    draft_response: str
    final_response: str
    paced_chunks: list
    # accumulating lists (use reducer)
    messages: Annotated[list, operator.add]
    persona_facts: Annotated[list, operator.add]
    emotional_events: Annotated[list, operator.add]
    # sub-schemas (replaced each turn or immutable)
    bot_mood: EmotionalState
    personality: Personality
    active_persona: PersonaConfig
    topic_state: TopicState
    # memory retrieval results
    recent_history: list
    long_term_facts: list
    # metadata
    turn_index: int
    last_updated: float
    # EMO-005: track consecutive negative turns
    consecutive_negative_turns: int
