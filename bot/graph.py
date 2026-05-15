"""
Build and return the compiled LangGraph StateGraph for the chatbot.

Node execution order:
  input_receiver
  → memory_retrieval
  → language_detector    (parallel with intent_analyzer is desirable but
  → intent_analyzer       LangGraph requires explicit parallel branching;
                          we keep sequential for simplicity and correctness)
  → emotional_update
  → mode_router
  → [conditional edge]
  → response_generator
  → humanizer_node
  → output_pacing
  → memory_writeback
  → END

GRAPH-004: graph.compile() is called with NO checkpointer.
GRAPH-002 Option B: mode_router writes response_mode; _route() only reads it.
"""
import logging
from langgraph.graph import StateGraph, END

from bot.config import AppConfig
from bot.state import ConversationState
from bot.modes import MODE_REGISTRY, DEFAULT_MODE

import bot.nodes.input_receiver as input_receiver
import bot.nodes.memory_retrieval as memory_retrieval
import bot.nodes.language_detector as language_detector
import bot.nodes.intent_analyzer as intent_analyzer
import bot.nodes.emotional_update as emotional_update
import bot.nodes.mode_router as mode_router
import bot.nodes.response_generator as response_generator
import bot.nodes.humanizer_node as humanizer_node
import bot.nodes.output_pacing as output_pacing
import bot.nodes.memory_writeback as memory_writeback

logger = logging.getLogger(__name__)


def _route(state: ConversationState) -> str:
    """
    Thin conditional edge function — ONLY reads response_mode from state.
    Contains no routing logic (GRAPH-002 Option B).
    """
    mode = state.get("response_mode", DEFAULT_MODE)
    return mode if mode in MODE_REGISTRY else DEFAULT_MODE


def build_graph(config: AppConfig):
    """Construct, wire, and compile the LangGraph StateGraph."""
    graph = StateGraph(ConversationState)

    # Register nodes
    graph.add_node("input_receiver", input_receiver.run)
    graph.add_node("memory_retrieval", memory_retrieval.make(config))
    graph.add_node("language_detector", language_detector.run)
    graph.add_node("intent_analyzer", intent_analyzer.make(config))
    graph.add_node("emotional_update", emotional_update.run)
    graph.add_node("mode_router", mode_router.run)
    graph.add_node("response_generator", response_generator.make(config))
    graph.add_node("humanizer_node", humanizer_node.make(config))
    graph.add_node("output_pacing", output_pacing.make(config))
    graph.add_node("memory_writeback", memory_writeback.make(config))

    # Entry point
    graph.set_entry_point("input_receiver")

    # Sequential edges up to mode_router
    graph.add_edge("input_receiver", "memory_retrieval")
    graph.add_edge("memory_retrieval", "language_detector")
    graph.add_edge("language_detector", "intent_analyzer")
    graph.add_edge("intent_analyzer", "emotional_update")
    graph.add_edge("emotional_update", "mode_router")

    # Conditional edge after mode_router (GRAPH-002 Option B)
    # All modes currently map to the same response_generator node (GRAPH-003).
    graph.add_conditional_edges(
        "mode_router",
        _route,
        {mode: "response_generator" for mode in MODE_REGISTRY},
    )

    # Post-generation pipeline
    graph.add_edge("response_generator", "humanizer_node")
    graph.add_edge("humanizer_node", "output_pacing")
    graph.add_edge("output_pacing", "memory_writeback")
    graph.add_edge("memory_writeback", END)

    # Compile with NO checkpointer (GRAPH-004)
    compiled = graph.compile()
    logger.debug("Graph compiled successfully")
    return compiled
