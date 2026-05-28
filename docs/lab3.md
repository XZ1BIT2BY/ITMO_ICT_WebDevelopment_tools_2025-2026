# Лабораторная работа 3 — Docker, источники данных и очереди

## Описание

Упаковка FastAPI-приложения управления личными финансами в Docker, интеграция парсера курсов валют ЦБ РФ с базой данных, вызов парсера через HTTP и асинхронную очередь Celery + Redis.

## Архитектура

Система состоит из шести сервисов, управляемых через Docker Compose:

| Сервис | Образ | Порт | Описание |
|--------|-------|------|----------|
| `db` | postgres:16-alpine | 5432 | PostgreSQL |
| `redis` | redis:7-alpine | 6379 | Брокер Celery |
| `parser` | python:3.11-slim | 8001 | FastAPI-сервис парсера |
| `api` | python:3.11-slim | 8000 | Основное FastAPI-приложение |
| `celery_worker` | python:3.11-slim | — | Celery worker |
| `celery_beat` | python:3.11-slim | — | Celery beat (периодика) |

## Подзадача 1 — Упаковка в Docker

### Dockerfile основного приложения

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Dockerfile парсера

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Docker Compose

```yaml
services:
  db:
    image: postgres:16-alpine
    env_file: .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  parser:
    build:
      context: ./parser
    ports:
      - "8001:8001"
    depends_on:
      db:
        condition: service_healthy

  api:
    build:
      context: .
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build:
      context: .
    command: celery -A worker.celery_app:celery_app worker --loglevel=info
    depends_on:
      redis:
        condition: service_healthy

  celery_beat:
    build:
      context: .
    command: celery -A worker.celery_app:celery_app beat --loglevel=info
    depends_on:
      redis:
        condition: service_healthy
```

## Подзадача 2 — Парсер курсов ЦБ РФ

Парсер вынесен в отдельный FastAPI-сервис на порту 8001. Получает курсы валют с `cbr.ru` в формате XML и сохраняет в таблицу `exchange_rate`.

### Парсер (parser/main.py)

```python
@app.post("/parse", response_model=ParseResponse)
async def parse(request: ParseRequest):
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        rates = await fetch_rates(session, request.date_str)

    await save_rates_to_db(rates)

    return ParseResponse(
        message="Парсинг завершён успешно",
        date=request.date_str,
        count=len(rates),
        rates=rates[:5],
    )
```

### Сохранение в БД

```python
async def save_rates_to_db(rates: list[dict]) -> None:
    pool = await asyncpg.create_pool(DB_DSN)
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO exchange_rate (currency_code, currency_name, rate, date)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (currency_code, date)
            DO UPDATE SET rate = EXCLUDED.rate, currency_name = EXCLUDED.currency_name
            """,
            [
                (r["currency_code"], r["currency_name"], r["rate"],
                 date.fromisoformat(r["date"]))
                for r in rates
            ],
        )
```

### Эндпоинт в основном API для вызова парсера

```python
@router.post("/parser/parse")
def trigger_parse(request: ParseRequest):
    response = requests.post(
        f"{PARSER_URL}/parse",
        json={"date_str": request.date_str},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
```

## Подзадача 3 — Асинхронная очередь Celery

### Настройка Celery (worker/celery_app.py)

```python
celery_app = Celery(
    "finance_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    timezone="Europe/Moscow",
    beat_schedule={
        "parse-rates-every-day": {
            "task": "worker.celery_app.parse_rates_task",
            "schedule": crontab(hour=10, minute=0),
        },
    },
)
```

### Задача парсинга

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def parse_rates_task(self, date_str: str | None = None):
    if date_str is None:
        date_str = datetime.now().strftime("%d/%m/%Y")
    try:
        response = requests.post(
            f"{PARSER_URL}/parse",
            json={"date_str": date_str},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        raise self.retry(exc=exc)
```

### Эндпоинты для асинхронного вызова

```python
@router.post("/parser/parse/async")
def trigger_parse_async(request: ParseRequest):
    task = parse_rates_task.delay(request.date_str)
    return {"message": "Задача поставлена в очередь", "task_id": task.id}

@router.get("/parser/task/{task_id}")
def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": result.status}
```

## Эндпоинты парсера

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /parser/parse | Синхронный парсинг на указанную дату |
| POST | /parser/parse/today | Синхронный парсинг на сегодня |
| POST | /parser/parse/async | Асинхронный парсинг через Celery |
| POST | /parser/parse/today/async | Асинхронный парсинг на сегодня |
| GET | /parser/task/{task_id} | Статус и результат задачи Celery |

## Запуск

```bash
docker-compose up --build
```

После запуска:
- Основное API: http://localhost:8000/docs
- Парсер: http://localhost:8001/docs

## Ссылки
- [Код лабораторной](https://github.com/XZ1BIT2BY/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lab3)
