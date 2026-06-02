import streamlit as st
import chromadb
import ollama

from config import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBED_MODEL,
    CHAT_MODEL,
)


def get_embedding(text: str) -> list[float]:
    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text,
    )
    return response["embedding"]


def search_protocols(question: str, n_results: int = 8):
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception:
        st.error(
            "База протоколов ещё не создана. Сначала запусти ingest.py, чтобы проиндексировать Excel."
        )
        return []

    question_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results,
    )

    found = []

    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, metadata, distance in zip(docs, metadatas, distances):
        found.append(
            {
                "document": doc,
                "metadata": metadata,
                "distance": distance,
            }
        )

    return found


def build_prompt(question: str, found_items: list[dict]) -> str:
    context_parts = []

    for i, item in enumerate(found_items, start=1):
        metadata = item["metadata"]
        document = item["document"]

        context_parts.append(
            f"""
Источник {i}:
{metadata["source_ref"]}

Текст:
{document}
"""
        )

    context = "\n\n".join(context_parts)

    return f"""
Ты помощник по протоколам совещаний.

Отвечай только на основании найденных пунктов протоколов.
Не придумывай факты, даты, номера протоколов и номера пунктов.
Если информации недостаточно, так и скажи.

В ответе обязательно указывай источники в формате:
[Протокол №..., дата ..., пункт ...]

Вопрос пользователя:
{question}

Найденные пункты:
{context}

Сформируй краткий, понятный и проверяемый ответ.
"""


def generate_answer(question: str, found_items: list[dict]) -> str:
    prompt = build_prompt(question, found_items)

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response["message"]["content"]


st.set_page_config(
    page_title="Поиск по протоколам",
    layout="wide",
)

st.title("Поиск по протоколам совещаний")

question = st.text_input("Введите вопрос по протоколам:")

n_results = st.slider(
    "Сколько пунктов искать",
    min_value=3,
    max_value=20,
    value=8,
)

if st.button("Найти ответ") and question.strip():
    with st.spinner("Ищу релевантные пункты..."):
        found_items = search_protocols(question, n_results=n_results)

    if not found_items:
        st.stop()



    st.subheader("Найденные пункты")

    for i, item in enumerate(found_items, start=1):
        metadata = item["metadata"]

        with st.expander(f"{i}. {metadata['source_ref']}"):
            st.write(item["document"])
            st.caption(f"distance: {item['distance']}")

    with st.spinner("Формирую ответ..."):
        answer = generate_answer(question, found_items)

    st.subheader("Ответ")
    st.write(answer)