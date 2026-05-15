"""
NODE-006: response_generator

Single generation node parameterized by mode config. Builds a system prompt
using mood_to_description() and persona_to_description() (never raw floats),
adds a language/script instruction, and calls the LLM.

Appends an AIMessage to messages, writes draft_response.
"""
import logging
from langchain_core.messages import SystemMessage, AIMessage
from bot.config import AppConfig
from bot.llm import get_llm
from bot.modes import MODE_REGISTRY, DEFAULT_MODE
from bot.mood import mood_to_description
from bot.persona import persona_to_description
from bot.state import ConversationState

logger = logging.getLogger(__name__)


def make(config: AppConfig):
    """Factory that closes over config and returns the async node function."""

    async def run(state: ConversationState) -> dict:
        response_mode = state.get("response_mode", DEFAULT_MODE)
        if response_mode not in MODE_REGISTRY:
            response_mode = DEFAULT_MODE

        mode_cfg = MODE_REGISTRY[response_mode]
        model_key = mode_cfg["model_key"]
        temperature = mode_cfg["temperature"]
        max_tokens = mode_cfg["max_tokens"]
        prompt_summary = mode_cfg["prompt_summary"]

        mood = state.get("bot_mood")
        personality = state.get("personality")
        active_persona = state.get("active_persona")
        detected_language = state.get("detected_language", "en")
        detected_script = state.get("detected_script", "Latn")
        long_term_facts = state.get("long_term_facts", [])
        messages = state.get("messages", [])

        # Build natural-language descriptions (never raw floats/enum strings)
        mood_desc = mood_to_description(mood) if mood else "feeling relatively neutral and balanced"
        persona_desc = persona_to_description(active_persona) if active_persona else "You are a helpful conversational assistant."

        # Language instruction (NODE-006 requirement)
        lang_instruction = _build_language_instruction(detected_language, detected_script)

        # Assemble system prompt
        system_parts = [
            persona_desc,
            f"Right now you are {mood_desc}. Let this subtly shape your tone without stating it explicitly.",
            f"Style guideline: {prompt_summary}",
            lang_instruction,
        ]

        if long_term_facts:
            facts_block = "\n".join(f"- {f}" for f in long_term_facts)
            system_parts.append(f"Relevant past context:\n{facts_block}")

        system_prompt = "\n\n".join(system_parts)

        # Build messages list for LLM: system + conversation history
        llm_messages = [SystemMessage(content=system_prompt)] + list(messages)

        try:
            llm = get_llm(config, model_key=model_key)

            # Apply temperature and max_tokens if the model supports it
            llm_with_opts = llm.bind(
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response = await llm_with_opts.ainvoke(llm_messages)
            draft = response.content

        except Exception as e:
            logger.error("NODE-006 LLM call failed: %s", e)
            draft = "I'm sorry, I'm having trouble generating a response right now."

        logger.debug("NODE-006 mode=%s draft_len=%d", response_mode, len(draft))

        return {
            "draft_response": draft,
            "messages": [AIMessage(content=draft)],
        }

    return run


def _build_language_instruction(language: str, script: str) -> str:
    """Build a natural language instruction to respond in the detected language/script."""
    # Map BCP-47 tags to friendly names for the most common cases
    lang_names = {
        "en": "English",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "it": "Italian",
        "pt": "Portuguese",
        "nl": "Dutch",
        "ru": "Russian",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
        "hi": "Hindi",
        "pl": "Polish",
        "sv": "Swedish",
        "tr": "Turkish",
    }
    # Map ISO 15924 codes to friendly names
    script_names = {
        "Latn": "Latin script",
        "Cyrl": "Cyrillic script",
        "Hans": "Simplified Chinese characters",
        "Arab": "Arabic script",
        "Hebr": "Hebrew script",
        "Deva": "Devanagari script",
        "Grek": "Greek script",
        "Kana": "Japanese kana",
    }

    lang_name = lang_names.get(language, language)
    script_name = script_names.get(script, script)

    return f"Respond in {lang_name} using {script_name}."
