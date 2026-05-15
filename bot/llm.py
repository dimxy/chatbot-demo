import os
import logging
from langchain_core.language_models import BaseChatModel
from bot.config import AppConfig

logger = logging.getLogger(__name__)


def get_llm(config: AppConfig, model_key: str = "response_generator") -> BaseChatModel:
    """Return a LangChain BaseChatModel for the given model key."""
    model_name = getattr(config.llm.models, model_key)
    if config.llm.provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model_name, base_url=config.llm.ollama.base_url)
    else:
        from langchain_openai import ChatOpenAI
        api_key = os.environ.get(config.llm.openai.api_key_env)
        return ChatOpenAI(model=model_name, api_key=api_key)


def validate_provider(config: AppConfig) -> None:
    """Validate that the configured LLM provider is reachable."""
    if config.llm.provider == "ollama":
        import urllib.request
        try:
            urllib.request.urlopen(
                f"{config.llm.ollama.base_url}/api/tags", timeout=3
            )
        except Exception:
            raise RuntimeError(
                f"Ollama not reachable at {config.llm.ollama.base_url}. "
                "Start Ollama or switch provider to 'openai' in config.yaml."
            )
    else:
        key_name = config.llm.openai.api_key_env
        if not os.environ.get(key_name):
            raise RuntimeError(
                f"OpenAI API key not found. Set the {key_name} environment variable."
            )
