"""Database schema for the initial application skeleton."""

SCHEMA_VERSION = 1

CREATE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS task_model_configs (
    task TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model_name TEXT,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

DEFAULT_MODEL_CONFIGS = (
    ("classification", "ollama", "gemma4:e2b", 1),
    ("renaming", "ollama", "gemma4:e2b", 1),
    ("vision", "ollama", None, 0),
    ("embeddings", "ollama", None, 0),
)

