# Практика 1.3 — Alembic, .env, .gitignore

## Описание
Настройка системы миграций через Alembic, хранение секретов в .env файле.

## Подключение к БД через .env

```python
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine

load_dotenv()
DB_ADMIN = os.getenv("DB_ADMIN")
engine = create_engine(DB_ADMIN, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

## .env файл
DB_ADMIN=postgresql://postgres:8118@localhost/finance_db

## .gitignore
pycache/
*.py[cod]
.env
venv/
.venv/
*.db

## migrations/env.py

```python
import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from models import User, Account, Category, Transaction, Tag, TransactionTag

config = context.config
config.set_main_option("sqlalchemy.url", os.getenv("DB_ADMIN"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Ссылки
- [Коммит практики 1.3](https://github.com/XZ1BIT2BY/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lab1/students/K3340/Shestak_Bogdan/practics/practic_3)