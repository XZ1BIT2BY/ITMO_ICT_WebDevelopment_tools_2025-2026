import os
import requests
from celery import Celery
from celery.schedules import crontab
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
PARSER_URL = os.getenv("PARSER_URL", "http://parser:8001")

celery_app = Celery(
    "finance_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=True,
    # Периодические задачи (Задача 3 — periodic tasks)
    beat_schedule={
        "parse-rates-every-day": {
            "task": "worker.celery_app.parse_rates_task",
            "schedule": crontab(hour=10, minute=0),  # каждый день в 10:00 МСК
            "args": [datetime.now().strftime("%d/%m/%Y")],
        },
    },
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def parse_rates_task(self, date_str: str | None = None):
    """
    Celery-задача: вызывает парсер-сервис по HTTP и возвращает результат.
    date_str: "DD/MM/YYYY". Если None — берётся сегодняшняя дата.
    """
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
