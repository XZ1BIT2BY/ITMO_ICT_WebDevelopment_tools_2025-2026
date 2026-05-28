# Лабораторная работа 1 — Сервис управления личными финансами

## Описание
Полноценное серверное приложение на FastAPI с PostgreSQL, JWT-авторизацией и системой миграций Alembic.

## Модели БД

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str

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

class TransactionTag(SQLModel, table=True):
    transaction_id: Optional[int] = Field(
        default=None, foreign_key="transaction.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="tag.id", primary_key=True
    )
    note: str  # доп. поле ассоциативной сущности
```

## Подключение к БД

```python
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine

load_dotenv()
db_url = os.getenv("DB_ADMIN")
engine = create_engine(db_url, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

## Авторизация

### Хэширование паролей

```python
import hashlib, os, hmac

def hash_password(plain_password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, iterations=260_000)
    return salt.hex() + ":" + key.hex()

def verify_password(plain_password: str, hashed: str) -> bool:
    salt_hex, key_hex = hashed.split(":")
    salt = bytes.fromhex(salt_hex)
    stored_key = bytes.fromhex(key_hex)
    new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt, iterations=260_000)
    return hmac.compare_digest(stored_key, new_key)
```

### Генерация JWT

```python
def create_access_token(user_id: int, username: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": int(time.time()) + 86400,
        "iat": int(time.time()),
    }
    header_enc = _b64url_encode(json.dumps(header).encode())
    payload_enc = _b64url_encode(json.dumps(payload).encode())
    signing_input = f"{header_enc}.{payload_enc}"
    signature = hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"
```

## Эндпоинты

### Auth
| Метод | URL | Описание |
|-------|-----|----------|
| POST | /auth/register | Регистрация |
| POST | /auth/login | Авторизация, возвращает JWT |

### Users
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /users/me | Профиль текущего пользователя |
| GET | /users/ | Список пользователей |
| PATCH | /users/me/password | Смена пароля |

### Accounts
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /accounts/ | Список счетов |
| GET | /accounts/{id} | Получить счёт |
| POST | /accounts/ | Создать счёт |
| PATCH | /accounts/{id} | Обновить счёт |
| DELETE | /accounts/{id} | Удалить счёт |

### Categories
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /categories/ | Список категорий |
| GET | /categories/{id} | Получить категорию |
| POST | /categories/ | Создать категорию |
| PATCH | /categories/{id} | Обновить категорию |
| DELETE | /categories/{id} | Удалить категорию |

### Transactions
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /transactions/ | Список транзакций |
| GET | /transactions/{id} | Получить транзакцию |
| POST | /transactions/ | Создать транзакцию |
| PATCH | /transactions/{id} | Обновить транзакцию |
| DELETE | /transactions/{id} | Удалить транзакцию |

### Tags
| Метод | URL | Описание |
|-------|-----|----------|
| GET | /tags/ | Список тегов |
| POST | /tags/ | Создать тег |
| DELETE | /tags/{id} | Удалить тег |
| POST | /tags/transaction/{t_id}/tag/{tag_id} | Привязать тег к транзакции |
| DELETE | /tags/transaction/{t_id}/tag/{tag_id} | Отвязать тег |

## Ссылки
- [Код лабораторной](https://github.com/XZ1BIT2BY/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lab1/students/K3340/Shestak_Bogdan/lab1)