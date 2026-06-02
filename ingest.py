import pandas as pd
import chromadb
import ollama

from config import (
    EXCEL_PATH,
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBED_MODEL,
    COL_PROTOCOL_NUMBER,
    COL_PROTOCOL_DATE,
    COL_ITEM_NUMBER,
    COL_ITEM_TEXT,
    OLLAMA_HOST,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

ollama_client = ollama.Client(host=OLLAMA_HOST)


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def make_source_ref(row) -> str:
    protocol_number = normalize_text(row[COL_PROTOCOL_NUMBER])
    protocol_date = normalize_text(row[COL_PROTOCOL_DATE])
    item_number = normalize_text(row[COL_ITEM_NUMBER])

    return f"Протокол №{protocol_number} от {protocol_date}, пункт {item_number}"


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Режем длинный текст на куски.
    overlap нужен, чтобы смысл на границе кусков не терялся.
    """
    text = normalize_text(text)

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        next_start = end - overlap
        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def get_embedding(text: str) -> list[float]:
    response = ollama_client.embeddings(
        model=EMBED_MODEL,
        prompt=text,
    )
    return response["embedding"]


def main():
    print(f"Excel: {EXCEL_PATH}")
    print(f"Vector DB: {CHROMA_PATH}")
    print(f"Ollama: {OLLAMA_HOST}")
    print(f"Embedding model: {EMBED_MODEL}")

    if not EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"Excel-файл не найден: {EXCEL_PATH}. "
            "Положи файл в data/protocols.xlsx или задай EXCEL_PATH."
        )

    df = pd.read_excel(EXCEL_PATH)

    required_columns = [
        COL_PROTOCOL_NUMBER,
        COL_PROTOCOL_DATE,
        COL_ITEM_NUMBER,
        COL_ITEM_TEXT,
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"В Excel не найдены колонки: {missing}")

    df = df.copy()
    df[COL_ITEM_TEXT] = df[COL_ITEM_TEXT].apply(normalize_text)
    df = df[df[COL_ITEM_TEXT] != ""]

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(name=COLLECTION_NAME)

    documents = []
    embeddings = []
    metadatas = []
    ids = []

    total_chunks = 0
    failed_chunks = 0

    for index, row in df.iterrows():
        item_text = normalize_text(row[COL_ITEM_TEXT])
        source_ref = make_source_ref(row)

        chunks = split_text(item_text)

        if len(chunks) > 1:
            print(f"Длинный пункт разбит на {len(chunks)} частей: {source_ref}")

        for chunk_index, chunk in enumerate(chunks, start=1):
            document = f"{source_ref}\n\n{chunk}"

            metadata = {
                "protocol_number": normalize_text(row[COL_PROTOCOL_NUMBER]),
                "protocol_date": normalize_text(row[COL_PROTOCOL_DATE]),
                "item_number": normalize_text(row[COL_ITEM_NUMBER]),
                "source_ref": source_ref,
                "chunk_index": chunk_index,
                "chunks_total": len(chunks),
            }

            doc_id = (
                f"{metadata['protocol_number']}_"
                f"{metadata['item_number']}_"
                f"{index}_chunk_{chunk_index}"
            )

            print(f"Индексируем: {source_ref}, часть {chunk_index}/{len(chunks)}")

            try:
                embedding = get_embedding(document)
            except Exception as e:
                failed_chunks += 1
                print("ОШИБКА при создании embedding")
                print(f"Источник: {source_ref}")
                print(f"Длина текста: {len(document)} символов")
                print(f"Ошибка: {e}")
                continue

            documents.append(document)
            embeddings.append(embedding)
            metadatas.append(metadata)
            ids.append(doc_id)

            total_chunks += 1

    if not documents:
        raise ValueError("Не удалось создать ни одного документа для индексации.")

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    print(f"Готово. Строк Excel обработано: {len(df)}")
    print(f"Кусков добавлено в базу: {total_chunks}")
    print(f"Кусков с ошибкой: {failed_chunks}")


if __name__ == "__main__":
    main()
