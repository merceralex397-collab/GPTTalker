"""Context collection definitions and helpers for GPTTalker."""

from dataclasses import dataclass
from enum import StrEnum


class ContextCollection(StrEnum):
    """Enumeration of context collections in Qdrant."""

    FILES = "gpttalker_files"
    ISSUES = "gpttalker_issues"
    SUMMARIES = "gpttalker_summaries"


@dataclass(frozen=True)
class CollectionConfig:
    """Configuration for a Qdrant collection."""

    name: str
    description: str
    vector_size: int
    distance_metric: str = "Cosine"
    hnsw_m: int = 16
    hnsw_ef_construct: int = 128
    hnsw_full_scan_threshold: int = 10000

    def __str__(self) -> str:
        return f"CollectionConfig(name={self.name}, vectors={self.vector_size})"


# Collection configurations
COLLECTION_CONFIGS: dict[ContextCollection, CollectionConfig] = {
    ContextCollection.FILES: CollectionConfig(
        name=ContextCollection.FILES.value,
        description="Indexed file contents for semantic search",
        vector_size=1536,  # OpenAI ada-002 compatible
    ),
    ContextCollection.ISSUES: CollectionConfig(
        name=ContextCollection.ISSUES.value,
        description="Known issues with descriptions for semantic search",
        vector_size=1536,
    ),
    ContextCollection.SUMMARIES: CollectionConfig(
        name=ContextCollection.SUMMARIES.value,
        description="Extracted code summaries per file for semantic search",
        vector_size=1536,
    ),
}


def get_collection_config(collection: ContextCollection) -> CollectionConfig:
    """Get the configuration for a specific collection.

    Args:
        collection: The context collection to get config for.

    Returns:
        CollectionConfig instance.

    Raises:
        ValueError: If collection is not recognized.
    """
    config = COLLECTION_CONFIGS.get(collection)
    if config is None:
        raise ValueError(f"Unknown collection: {collection}")
    return config


def get_all_collections() -> list[CollectionConfig]:
    """Get configurations for all collections.

    Returns:
        List of all CollectionConfig instances.
    """
    return list(COLLECTION_CONFIGS.values())


# Indexable payload fields for filtering
INDEXABLE_FIELDS = {
    ContextCollection.FILES: [
        "repo_id",
        "node_id",
        "extension",
        "content_hash",
        "language",
        "size_bytes",
        "indexed_at",
    ],
    ContextCollection.ISSUES: [
        "repo_id",
        "status",
        "created_at",
        "updated_at",
        "indexed_at",
    ],
    ContextCollection.SUMMARIES: [
        "repo_id",
        "node_id",
        "file_id",
        "language",
        "indexed_at",
    ],
}


def get_indexable_fields(collection: ContextCollection) -> list[str]:
    """Get list of indexable/filterable fields for a collection.

    Args:
        collection: The context collection.

    Returns:
        List of field names that can be used for filtering.
    """
    return INDEXABLE_FIELDS.get(collection, [])


# File type to language mapping
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".md": "markdown",
    ".txt": "text",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".pl": "perl",
    ".lua": "lua",
    ".r": "r",
    ".scala": "scala",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".clj": "clojure",
    ".ml": "ocaml",
    ".fs": "fsharp",
    ".vue": "vue",
    ".svelte": "svelte",
    ".xml": "xml",
    ".svg": "svg",
}


def detect_language(extension: str) -> str | None:
    """Detect programming language from file extension.

    Args:
        extension: File extension (e.g., '.py', '.js').

    Returns:
        Language name or None if unknown.
    """
    return EXTENSION_TO_LANGUAGE.get(extension.lower())


# Default allowed extensions for indexing
ALLOWED_INDEX_EXTENSIONS: set[str] = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sh",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".swift",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".sql",
    ".html",
    ".css",
    ".scss",
    ".vue",
    ".svelte",
    ".xml",
}


def is_indexable(extension: str) -> bool:
    """Check if a file extension is allowed for indexing.

    Args:
        extension: File extension to check.

    Returns:
        True if the extension is allowed for indexing.
    """
    return extension.lower() in ALLOWED_INDEX_EXTENSIONS
