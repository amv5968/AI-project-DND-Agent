"""
Configuration for the course project AI Dungeon Master.
"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

MODEL_NAME = "llama3.2:latest"
EMBEDDING_MODEL = "nomic-embed-text"
RAG_COLLECTION = "dnd_project_lore"
RAG_PERSIST_DIR = str(BASE_DIR / "chroma_store")
SQLITE_DB_PATH = str(BASE_DIR / "game_state.db")

DEFAULT_TEMPERATURE = 0.4
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 500
DEFAULT_NUM_CONTEXT_CHUNKS = 3

SYSTEM_TEMPLATE_FILE = str(BASE_DIR / "templates" / "dm_system_template.json")
DEFAULT_DATA_DIR = str(BASE_DIR / "data")
