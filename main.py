"""
main.py — CLI entry point for the human-like conversational bot.

Usage:
  python main.py [--config PATH] [--persona NAME]

Ctrl+C exits cleanly. Non-TTY stdin auto-disables pacing.
"""
import argparse
import asyncio
import logging
import signal
import sys
import time
import uuid

from bot.config import load_config
from bot.graph import build_graph
from bot.llm import validate_provider
from bot.state import (
    ConversationState,
    EmotionalState,
    Personality,
    PersonaConfig,
    TopicState,
)

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s %(message)s",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Human-like conversational bot")
    p.add_argument("--config", help="Path to config.yaml")
    p.add_argument("--persona", help="Persona name to use")
    p.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return p.parse_args()


def select_persona(config, name: str | None) -> PersonaConfig:
    """Select a persona from config by name, or default to the first one."""
    if not config.personas:
        return PersonaConfig(name="Bot", gender="neutral")

    if name is None:
        entry = config.personas[0]
    else:
        matches = [p for p in config.personas if p.name.lower() == name.lower()]
        if not matches:
            names = ", ".join(p.name for p in config.personas)
            print(
                f"Unknown persona '{name}'. Available: {names}",
                file=sys.stderr,
            )
            sys.exit(1)
        entry = matches[0]

    return PersonaConfig(
        name=entry.name,
        gender=entry.gender,
        emotional_distance=entry.emotional_distance,
        warmth=entry.warmth,
        sexuality=entry.sexuality,
        playfulness=entry.playfulness,
    )


def create_initial_state(config, persona: PersonaConfig) -> dict:
    """Build the initial ConversationState dict for a new session."""
    p = config.personality
    return {
        "messages": [],
        "persona_facts": [],
        "emotional_events": [],
        "bot_mood": EmotionalState(),
        "personality": Personality(
            baseline_valence=p.baseline_valence,
            baseline_arousal=p.baseline_arousal,
            baseline_dominance=p.baseline_dominance,
            emotional_volatility=p.emotional_volatility,
            decay_rate=p.decay_rate,
            expressiveness=p.expressiveness,
        ),
        "active_persona": persona,
        "topic_state": TopicState(),
        "turn_index": 0,
        "last_updated": time.time(),
        "conversation_id": str(uuid.uuid4()),
        "detected_language": "en",
        "detected_script": "Latn",
        "response_mode": "default",
        "long_term_facts": [],
        "recent_history": [],
        "consecutive_negative_turns": 0,
    }


async def run_session(config, persona: PersonaConfig) -> None:
    """Main REPL loop. Reads from stdin, invokes graph, prints response."""
    is_tty = sys.stdout.isatty()

    # Auto-disable pacing for piped/non-interactive input
    if not is_tty:
        config.pacing.enabled = False

    graph = build_graph(config)
    state = create_initial_state(config, persona)

    print(f"[{persona.name}] Ready. Type your message (Ctrl+C to exit).\n")

    shutdown = False

    def handle_sigint(sig, frame):
        nonlocal shutdown
        shutdown = True

    signal.signal(signal.SIGINT, handle_sigint)

    loop = asyncio.get_event_loop()

    while not shutdown:
        try:
            # Prompt
            if is_tty:
                print("You: ", end="", flush=True)

            # Read line asynchronously without blocking the event loop
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                # EOF
                break

            user_input = line.strip()
            if not user_input:
                continue

            # Merge new input into accumulated state
            state = {**state, "raw_user_message": user_input}

            # Run graph (full state round-trip; no checkpointer)
            state = await graph.ainvoke(state)

            # Output response, respecting pacing if enabled
            chunks = state.get("paced_chunks") or [state.get("final_response", "")]
            if is_tty:
                print(f"{persona.name}: ", end="", flush=True)

            for i, chunk in enumerate(chunks):
                is_last = i == len(chunks) - 1
                print(chunk, end="\n" if is_last else " ", flush=True)

                # Apply pacing delay between chunks (not after last chunk)
                if is_tty and config.pacing.enabled and not is_last:
                    mood = state.get("bot_mood")
                    arousal = mood.arousal if mood else 0.3
                    delay = min(
                        (1.0 - arousal) * 1.5 + 0.3,
                        config.pacing.max_chunk_delay,
                    )
                    await asyncio.sleep(delay)

        except KeyboardInterrupt:
            break
        except ValueError as e:
            # e.g. empty message validation error from NODE-001
            print(f"[error] {e}", flush=True)
        except Exception as e:
            logging.getLogger(__name__).exception("Unexpected error in session loop")
            print(f"[error] Unexpected error: {e}", file=sys.stderr, flush=True)

    print("\nSession ended.")


def main() -> None:
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    config = load_config(args.config)
    validate_provider(config)
    persona = select_persona(config, args.persona)

    asyncio.run(run_session(config, persona))


if __name__ == "__main__":
    main()
