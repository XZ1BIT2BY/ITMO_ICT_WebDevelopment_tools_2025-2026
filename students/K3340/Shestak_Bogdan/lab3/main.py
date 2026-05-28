from fastapi import FastAPI
from db import init_db
from app.routers import auth, users, accounts, categories, transactions, tags
from app.routers import parser  # новый роутер для лабы 3

app = FastAPI(
    title="Finance API",
    description="Сервис управления личными финансами",
    version="2.0.0",
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(tags.router)
app.include_router(parser.router)  # /parser/parse, /parser/parse/async и т.д.
