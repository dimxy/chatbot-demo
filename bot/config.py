import os
import yaml
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class OllamaConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_url: str = "http://localhost:11434"


class OpenAIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key_env: str = "OPENAI_API_KEY"


class ModelNamesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent_analyzer: str = "llama3.2:3b"
    response_generator: str = "llama3.1:8b"


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["ollama", "openai"] = "ollama"
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    models: ModelNamesConfig = Field(default_factory=ModelNamesConfig)


class MemoryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    short_term_turns: int = 20
    long_term_top_k: int = 3
    qdrant_path: str = ".qdrant"


class PacingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    max_chunk_delay: float = 4.0


class HumanizerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intensity: float = 0.7


class PersonaConfigEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    gender: str
    emotional_distance: float = 0.5
    warmth: float = 0.6
    sexuality: Literal["interested", "distracted"] = "distracted"
    playfulness: float = 0.5


class PersonalityConfigEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    baseline_valence: float = 0.1
    baseline_arousal: float = 0.3
    baseline_dominance: float = 0.0
    emotional_volatility: float = 0.5
    decay_rate: float = 0.2
    expressiveness: float = 0.6


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    pacing: PacingConfig = Field(default_factory=PacingConfig)
    humanizer: HumanizerConfig = Field(default_factory=HumanizerConfig)
    personas: list[PersonaConfigEntry] = Field(default_factory=list)
    personality: PersonalityConfigEntry = Field(default_factory=PersonalityConfigEntry)


def load_config(config_path: Optional[str] = None) -> AppConfig:
    path = config_path or os.environ.get("CONFIG_PATH") or "config.yaml"
    if os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    return AppConfig.model_validate(data)
