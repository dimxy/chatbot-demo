# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Python CLI chatbot built on LangGraph with persistent emotional state, mood-driven responses, and human-like disfluencies. The full specification is in `REQS.yaml` — consult it for acceptance criteria before implementing any node or schema.

## Commands

```bash
python main.py                        # start interactive REPL
python main.py --config path/to.yaml  # use a specific config file
python -m pytest                      # run all tests
python -m pytest tests/test_foo.py::test_bar  # run a single test
```

Pacing is auto-disabled when stdout is not a TTY (piped input).

## Architecture

### Graph pipeline (LangGraph `StateGraph`)

Nodes execute in this order; NODE-010 runs **in parallel with NODE-003**:

```
NODE-001 input_receiver
  ├── NODE-010 language_detector   (parallel)
  └── NODE-003 intent_mood_analyzer (parallel)
NODE-004 emotional_state_update
NODE-005 response_mode_router  ──→  conditional edge  ──→  NODE-006
NODE-006 response_generator
NODE-007 humanizer
NODE-008 output_pacing
NODE-009 memory_writeback
```

### Routing — Option B (GRAPH-002)

NODE-005 is a **regular node** that writes `response_mode` to state. A thin conditional edge function reads that field and returns the node key — it contains no logic. Do **not** implement routing as a conditional edge function that bypasses the node.

### No LangGraph checkpointing (GRAPH-004)

`graph.compile()` is called **without a checkpointer**. Do not import or use `MemorySaver`, `SqliteSaver`, or any `langgraph.checkpoint.*` class. All persistence is handled by NODE-002 (retrieval) and NODE-009 (writeback).

### Emotional state update order (EMO-001)

Each turn the update MUST follow: **decay → stimulus → clamp → trigger detection**. Applying decay after stimulus would erase the message's impact. See `REQS.yaml` EMO-002/EMO-003 for the exact formulas.

### LLM provider abstraction (NFR-007)

No node instantiates a provider client directly. All LLM calls go through a shared abstraction keyed by `config.llm.provider` (`ollama` or `openai`). Model names are resolved per-node from `config.llm.models.*`. Default provider is `ollama` (no API key required).

### Language detection (NODE-010)

Uses an **offline library** (e.g. `lingua`, `langdetect`, `fasttext-langdetect`) — no LLM call. Outputs BCP-47 language tag and ISO 15924 script code, which NODE-006 injects into the system prompt as a plain-English instruction. Falls back to `en`/`Latn` on failure.

### Long-term memory (MEM-002)

Vector store is **Qdrant in local-directory mode**: `QdrantClient(path=<local_path>)`. Never use `url=` or `host=`. Default path is `.qdrant/` relative to the working directory. Collection is auto-created on first run.

### Humanizer (NODE-007)

Pure text post-processing — **not an LLM call**. Injects disfluencies, hedges, and fragments based on `personality.expressiveness` and `bot_mood`. At `expressiveness=0` output is unchanged. Accepts an optional `seed` for deterministic test output.

### Configuration (NFR-006/NFR-007)

`config.yaml` is the single source of truth for all tunable parameters. Resolution order: `--config` CLI flag → `CONFIG_PATH` env var → `config.yaml` in working directory. Unknown keys raise an error at startup. A default `config.yaml` ships with the repo.

### Mood representation

Numeric `EmotionalState` (valence, arousal, dominance) is **never passed raw to any LLM**. Call `mood_to_description(bot_mood)` to get a short natural-language string before injecting into any prompt. Raw floats must not appear in `final_response`.
