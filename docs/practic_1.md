# Практика 1.1 — Базовое приложение FastAPI

## Описание
Реализация базового FastAPI приложения с виртуальной базой данных и Pydantic-моделями.

## Модели

```python
from pydantic import BaseModel
from typing import List, Optional

class Transaction(BaseModel):
    id: int
    amount: float
    description: str

class Account(BaseModel):
    id: int
    name: str
    balance: float
    transactions: Optional[List[Transaction]] = []
```

## Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | /accounts | Список всех счетов |
| GET | /account/{id} | Получить счёт по ID |
| POST | /account | Создать счёт |
| PUT | /account/{id} | Обновить счёт |
| DELETE | /account/{id} | Удалить счёт |

## Код эндпоинтов

```python
@app.get("/accounts")
def get_accounts():
    return temp_db

@app.get("/account/{acc_id}")
def get_account(acc_id: int):
    return [a for a in temp_db if a["id"] == acc_id]

@app.post("/account")
def create_account(acc: dict):
    temp_db.append(acc)
    return {"status": 200, "data": acc}

@app.delete("/account/{acc_id}")
def delete_account(acc_id: int):
    for i, acc in enumerate(temp_db):
        if acc["id"] == acc_id:
            temp_db.pop(i)
            break
    return {"msg": "deleted"}

@app.put("/account/{acc_id}")
def update_account(acc_id: int, new_acc: dict):
    for i, acc in enumerate(temp_db):
        if acc["id"] == acc_id:
            temp_db[i] = new_acc
    return new_acc
```

## Ссылки
- [Коммит практики 1.1](https://github.com/XZ1BIT2BY/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lab1/students/K3340/Shestak_Bogdan/practics/practic_1)