from fastapi import FastAPI
from typing import List

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API работает"}

# временная БД
temp_db = [
    {
        "id": 1,
        "name": "Wallet",
        "balance": 1000,
        "transactions": []
    },
    {
        "id": 2,
        "name": "Card",
        "balance": 5000,
        "transactions": []
    }
]