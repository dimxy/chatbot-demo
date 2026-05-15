import logging
import time
import uuid
from typing import Optional
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

_client: Optional[QdrantClient] = None
COLLECTION = "conversations"


def get_client(path: str) -> QdrantClient:
    """Return a singleton QdrantClient using local-directory mode."""
    global _client
    if _client is None:
        _client = QdrantClient(path=path)
    return _client


def store_turn(
    client: QdrantClient,
    conversation_id: str,
    turn: int,
    user_msg: str,
    bot_response: str,
) -> None:
    """Persist a conversation turn to Qdrant via the fastembed add() interface."""
    doc = f"User: {user_msg}\nBot: {bot_response}"
    try:
        client.add(
            collection_name=COLLECTION,
            documents=[doc],
            metadata=[
                {
                    "conversation_id": conversation_id,
                    "turn": turn,
                    "ts": time.time(),
                }
            ],
            ids=[str(uuid.uuid4())],
        )
    except Exception as e:
        logger.warning("Qdrant write failed: %s", e)


def retrieve_relevant(
    client: QdrantClient,
    query: str,
    top_k: int = 3,
) -> list[str]:
    """Retrieve top-k relevant past turns via text-based vector search."""
    try:
        results = client.query(
            collection_name=COLLECTION,
            query_text=query,
            limit=top_k,
        )
        return [r.document for r in results]
    except Exception as e:
        logger.warning("Qdrant query failed: %s", e)
        return []


def get_short_term(messages: list, limit: int = 20) -> list:
    """Extract the most recent N turns from the message list (each turn = 2 messages)."""
    return messages[-(limit * 2):]
