import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult

router = APIRouter(prefix="/parser", tags=["parser"])

PARSER_URL = os.getenv("PARSER_URL", "http://parser:8001")


class ParseRequest(BaseModel):
    date_str: str  # "DD/MM/YYYY"


# ─── Подзадача 2: Синхронный вызов парсера через HTTP ────────────────────────

@router.post("/parse", summary="Синхронный запуск парсера курсов ЦБ РФ")
def trigger_parse(request: ParseRequest):
    """
    Отправляет запрос сервису-парсеру и ждёт ответа.
    Подходит для коротких вызовов; блокирует поток до завершения.
    """
    try:
        response = requests.post(
            f"{PARSER_URL}/parse",
            json={"date_str": request.date_str},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ошибка при обращении к парсеру: {e}")


@router.post("/parse/today", summary="Синхронный парсинг на сегодня")
def trigger_parse_today():
    """Вызывает парсер для получения курсов на сегодняшнюю дату."""
    try:
        response = requests.post(f"{PARSER_URL}/parse/today", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ошибка при обращении к парсеру: {e}")


# ─── Подзадача 3: Асинхронный вызов через Celery ─────────────────────────────

@router.post("/parse/async", summary="Асинхронный запуск парсера через очередь Celery")
def trigger_parse_async(request: ParseRequest):
    """
    Ставит задачу парсинга в очередь Celery/Redis и немедленно возвращает task_id.
    Результат можно получить через /parser/task/{task_id}.
    """
    from worker.celery_app import parse_rates_task

    task = parse_rates_task.delay(request.date_str)
    return {
        "message": "Задача поставлена в очередь",
        "task_id": task.id,
        "date_str": request.date_str,
    }


@router.post("/parse/today/async", summary="Асинхронный парсинг на сегодня")
def trigger_parse_today_async():
    """Ставит в очередь задачу парсинга курсов на сегодняшнюю дату."""
    from datetime import datetime
    from worker.celery_app import parse_rates_task

    today = datetime.now().strftime("%d/%m/%Y")
    task = parse_rates_task.delay(today)
    return {
        "message": "Задача поставлена в очередь",
        "task_id": task.id,
        "date_str": today,
    }


@router.get("/task/{task_id}", summary="Получить статус/результат задачи Celery")
def get_task_status(task_id: str):
    """Возвращает статус и результат задачи по её task_id."""
    from worker.celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)
    response = {
        "task_id": task_id,
        "status": result.status,
    }
    if result.ready():
        response["result"] = result.result if not isinstance(result.result, Exception) else str(result.result)
    return response
