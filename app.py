import chromadb
import ollama
import streamlit as st

from config import (
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBED_MODEL,
    CHAT_MODEL,
    OLLAMA_HOST,
    CONTACT_EMAIL,
    CONTACT_PHONE,
)

ollama_client = ollama.Client(host=OLLAMA_HOST)


def get_embedding(text: str) -> list[float]:
    response = ollama_client.embeddings(
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

    try:
        question_embedding = get_embedding(question)
    except Exception as exc:
        st.error(
            "Не удалось обратиться к Ollama. Проверь, что Ollama запущена и модель для embeddings скачана."
        )
        st.code(str(exc))
        return []

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results,
    )

    docs = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    found = []
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

    try:
        response = ollama_client.chat(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
    except Exception as exc:
        return (
            "Не удалось сформировать ответ через Ollama. "
            "Проверь, что чат-модель скачана и доступна.\n\n"
            f"Ошибка: {exc}"
        )

    return response["message"]["content"]


def render_feedback_block() -> None:
    st.markdown("---")
    st.subheader("Обратная связь")
    st.caption(
        "Если вы нашли ошибку в ответе, некорректный источник или не нашли нужную информацию, "
        "сообщите ответственному за систему."
    )

    contact_rows = []

    if CONTACT_EMAIL:
        contact_rows.append(f"**Email:** [{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL})")

    if CONTACT_PHONE:
        phone_href = CONTACT_PHONE.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        contact_rows.append(f"**Телефон:** [{CONTACT_PHONE}](tel:{phone_href})")

    if contact_rows:
        st.markdown("  \n".join(contact_rows))
    else:
        st.info("Контакты пока не указаны. Администратор может задать CONTACT_EMAIL и CONTACT_PHONE.")


st.set_page_config(
    page_title="Поиск по протоколам",
    layout="wide",
)

st.title("Поиск по протоколам совещаний")

with st.sidebar:
    st.subheader("Настройки")
    st.caption(f"Ollama: {OLLAMA_HOST}")
    st.caption(f"Embedding model: {EMBED_MODEL}")
    st.caption(f"Chat model: {CHAT_MODEL}")
    render_feedback_block()

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
        render_feedback_block()
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

render_feedback_block()
