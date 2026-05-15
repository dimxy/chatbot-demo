"""
NODE-010: language_detector

Detects BCP-47 language tag and ISO 15924 script code from the normalized
user message. Uses langdetect for language and Unicode character analysis
for script. Falls back to en/Latn on failure. No LLM call.
"""
import logging
import unicodedata
from bot.state import ConversationState

logger = logging.getLogger(__name__)

# Mapping from script keyword in Unicode char name to ISO 15924 code
_SCRIPT_MAP = [
    ("Latn", "LATIN"),
    ("Cyrl", "CYRILLIC"),
    ("Hans", "CJK"),
    ("Arab", "ARABIC"),
    ("Hebr", "HEBREW"),
    ("Deva", "DEVANAGARI"),
    ("Grek", "GREEK"),
    ("Kana", "HIRAGANA"),
    ("Kana", "KATAKANA"),
]


def detect_script(text: str) -> str:
    """Detect ISO 15924 script code via Unicode character name analysis."""
    counts: dict[str, int] = {}
    for ch in text:
        if not ch.isalpha():
            continue
        name = unicodedata.name(ch, "")
        for script, keyword in _SCRIPT_MAP:
            if keyword in name:
                counts[script] = counts.get(script, 0) + 1
                break
    return max(counts, key=counts.get) if counts else "Latn"


async def run(state: ConversationState) -> dict:
    message = state.get("normalized_message", "")

    detected_language = "en"
    detected_script = "Latn"

    if not message or len(message.strip()) < 3:
        logger.debug("NODE-010 message too short, defaulting to en/Latn")
        return {
            "detected_language": detected_language,
            "detected_script": detected_script,
        }

    # Language detection via langdetect
    try:
        from langdetect import detect as langdetect_detect
        detected_language = langdetect_detect(message)
    except Exception as e:
        logger.warning("NODE-010 langdetect failed: %s — defaulting to 'en'", e)
        detected_language = "en"

    # Script detection via Unicode analysis
    try:
        detected_script = detect_script(message)
    except Exception as e:
        logger.warning("NODE-010 script detection failed: %s — defaulting to 'Latn'", e)
        detected_script = "Latn"

    logger.debug(
        "NODE-010 lang=%s script=%s", detected_language, detected_script
    )

    return {
        "detected_language": detected_language,
        "detected_script": detected_script,
    }
