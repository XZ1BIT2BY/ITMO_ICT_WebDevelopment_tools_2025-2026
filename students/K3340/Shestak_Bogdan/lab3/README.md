# Лабораторная работа 3 — Docker, парсер, Celery

## Структура проекта

```
lab3/
├── Dockerfile              # образ основного FastAPI-приложения
├── docker-compose.yml      # оркестр всех сервисов
├── .env                    # переменные окружения
├── main.py                 # точка входа FastAPI (+ роутер парсера)
├── db.py                   # подключение к PostgreSQL
├── requirements.txt        # зависимости основного приложения
├── app/
│   ├── models.py
│   ├── auth/
│   └── routers/
│       ├── parser.py       # новые эндпоинты для вызова парсера
│       └── ...             # роутеры из lab1
├── parser/
│   ├── Dockerfile          # образ сервиса-парсера
│   ├── main.py             # FastAPI-приложение парсера
│   └── requirements.txt
└── worker/
    ├── __init__.py
    ├── celery_app.py       # Celery + периодические задачи
    └── requirements.txt
```

## Запуск

```bash
# Собрать и запустить все контейнеры
docker-compose up --build

# В фоне
docker-compose up --build -d
```

## Сервисы и порты

| Сервис         | Порт  | Описание                        |
|----------------|-------|---------------------------------|
| api            | 8000  | Основное FastAPI-приложение     |
| parser         | 8001  | Сервис парсера курсов ЦБ РФ    |
| db             | 5432  | PostgreSQL                      |
| redis          | 6379  | Redis (брокер Celery)           |
| celery_worker  | —     | Celery worker                   |
| celery_beat    | —     | Celery beat (периодика)         |

## API-эндпоинты парсера

### Подзадача 2 — Синхронный вызов

```
POST /parser/parse
Body: {"date_str": "28/05/2026"}
```

```
POST /parser/parse/today
```

### Подзадача 3 — Через очередь Celery

```
POST /parser/parse/async
Body: {"date_str": "28/05/2026"}
→ возвращает task_id

POST /parser/parse/today/async
→ возвращает task_id

GET /parser/task/{task_id}
→ статус и результат задачи
```

### Swagger UI

- Основное приложение: http://localhost:8000/docs
- Парсер: http://localhost:8001/docs

## Периодические задачи

Celery beat запускает парсинг курсов ЦБ РФ автоматически **каждый день в 10:00 МСК**.
Настройка находится в `worker/celery_app.py` → `beat_schedule`.
