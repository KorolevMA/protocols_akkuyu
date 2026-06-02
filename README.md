# protocols_akkuyu

Локальный/серверный RAG-поиск по протоколам совещаний.

## Что нужно положить вручную

Файл с протоколами не хранится в GitHub. На сервере положи Excel сюда:

```bash
data/protocols.xlsx
```

Минимальные колонки Excel:

```text
protocol_number
protocol_date
item_number
item_text
```

## Локальный запуск без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

ollama pull nomic-embed-text
ollama pull llama3.2:1b

python ingest.py
python -m streamlit run app.py
```

## Серверный запуск через Docker Compose

```bash
git clone https://github.com/KorolevMA/protocols_akkuyu.git
cd protocols_akkuyu
mkdir -p data vector_db
```

Загрузи Excel:

```bash
# файл должен оказаться здесь:
# protocols_akkuyu/data/protocols.xlsx
```

Запусти контейнеры:

```bash
docker compose up -d --build
```

Если Docker Hub ругается на pull rate limit, сначала выполни:

```bash
docker login
```

Скачай модели в контейнер Ollama:

```bash
docker exec -it protocols_ollama ollama pull nomic-embed-text
docker exec -it protocols_ollama ollama pull llama3.2:1b
```

Собери векторную базу:

```bash
docker compose run --rm app python ingest.py
```

Перезапусти приложение:

```bash
docker compose restart app
```

Проверка на сервере:

```bash
curl http://127.0.0.1:8501
```

## Доступ через Nginx

Приложение публикуется только локально на сервере:

```text
127.0.0.1:8501
```

Поэтому наружу его нужно отдавать через Nginx, домен, SSL и пароль.

Минимальная схема:

```text
https://your-domain.com -> Nginx -> http://127.0.0.1:8501
```

## Обновление протоколов

1. Замени файл:

```bash
data/protocols.xlsx
```

2. Пересобери индекс:

```bash
docker compose run --rm app python ingest.py
```

3. Перезапусти приложение:

```bash
docker compose restart app
```
