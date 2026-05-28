# Практика 1.2 — SQLModel и PostgreSQL

## Описание
Подключение к PostgreSQL через SQLModel, реализация ORM-моделей и CRUD через реальную БД.

## Подключение к БД

```python
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://postgres:8118@localhost/finance_db"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

## Модели

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str

class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: float
    user_id: int = Field(foreign_key="user.id")

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    account_id: int = Field(foreign_key="account.id")
    category_id: int = Field(foreign_key="category.id")

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

# Ассоциативная сущность many-to-many с доп. полем
class TransactionTag(SQLModel, table=True):
    transaction_id: Optional[int] = Field(
        default=None, foreign_key="transaction.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="tag.id", primary_key=True
    )
    note: str  # поле, характеризующее связь
```

## Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | /transactions | Список транзакций |
| POST | /transactions | Создать транзакцию |

## Код эндпоинтов

```python
@app.post("/transactions")
def create_tx(tx: Transaction, session: Session = Depends(get_session)):
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx

@app.get("/transactions")
def get_tx(session: Session = Depends(get_session)):
    return session.exec(select(Transaction)).all()
```

## Ссылки
- [Коммит практики 1.2](https://github.com/XZ1BIT2BY/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lab1/students/K3340/Shestak_Bogdan/practics/practic_2)