"""
NODE-008: output_pacing

Splits final_response into word-count chunks for simulated pacing.
When pacing is disabled, paced_chunks = [final_response].

Actual inter-chunk delays are applied in main.py during output,
since a graph node cannot stream directly to stdout between invocations.
This node prepares the chunks list.
"""
import logging
from bot.config import AppConfig
from bot.state import ConversationState

logger = logging.getLogger(__name__)

_WORDS_PER_CHUNK = 12


def make(config: AppConfig):
    """Factory that closes over config and returns the async node function."""

    async def run(state: ConversationState) -> dict:
        final = state.get("final_response", "")

        if not config.pacing.enabled:
            logger.debug("NODE-008 pacing disabled, single chunk")
            return {"paced_chunks": [final]}

        words = final.split()
        if not words:
            return {"paced_chunks": [final]}

        chunks = [
            " ".join(words[i : i + _WORDS_PER_CHUNK])
            for i in range(0, len(words), _WORDS_PER_CHUNK)
        ]

        logger.debug("NODE-008 split into %d chunks", len(chunks))
        return {"paced_chunks": chunks}

    return run
