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