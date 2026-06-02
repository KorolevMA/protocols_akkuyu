from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EXCEL_PATH = BASE_DIR / "data" / "protocols.xlsx"
CHROMA_PATH = BASE_DIR / "vector_db"

COL_PROTOCOL_NUMBER = "protocol_number"
COL_PROTOCOL_DATE = "protocol_date"
COL_ITEM_NUMBER = "item_number"
COL_ITEM_TEXT = "item_text"

EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.1:8b"
COLLECTION_NAME = "meeting_protocols"