from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

EXCEL_PATH = Path(os.getenv("EXCEL_PATH", BASE_DIR / "data" / "protocols.xlsx"))
CHROMA_PATH = Path(os.getenv("CHROMA_PATH", BASE_DIR / "vector_db"))

COL_PROTOCOL_NUMBER = os.getenv("COL_PROTOCOL_NUMBER", "protocol_number")
COL_PROTOCOL_DATE = os.getenv("COL_PROTOCOL_DATE", "protocol_date")
COL_ITEM_NUMBER = os.getenv("COL_ITEM_NUMBER", "item_number")
COL_ITEM_TEXT = os.getenv("COL_ITEM_TEXT", "item_text")

EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2:1b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "meeting_protocols")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
