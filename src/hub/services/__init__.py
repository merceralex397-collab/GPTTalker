"""GPTTalker hub services."""

from .context_collections import (
    ALLOWED_INDEX_EXTENSIONS,
    COLLECTION_CONFIGS,
    ContextCollection,
    detect_language,
    get_all_collections,
    get_collection_config,
    get_indexable_fields,
    is_indexable,
)
from .node_health import NodeHealth, NodeHealthService
from .qdrant_client import (
    COLLECTION_FILES,
    COLLECTION_ISSUES,
    COLLECTION_SUMMARIES,
    QdrantClientWrapper,
    create_qdrant_client,
    get_qdrant_client,
)

__all__ = [
    # Context collections
    "ContextCollection",
    "COLLECTION_CONFIGS",
    "COLLECTION_FILES",
    "COLLECTION_ISSUES",
    "COLLECTION_SUMMARIES",
    "get_all_collections",
    "get_collection_config",
    "get_indexable_fields",
    "detect_language",
    "is_indexable",
    "ALLOWED_INDEX_EXTENSIONS",
    # Node health
    "NodeHealth",
    "NodeHealthService",
    # Qdrant client
    "QdrantClientWrapper",
    "get_qdrant_client",
    "create_qdrant_client",
]
