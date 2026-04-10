from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from db import init_db, get_session
from models import Transaction

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Works!"}

@app.on_event("startup")
def startup():
    init_db()