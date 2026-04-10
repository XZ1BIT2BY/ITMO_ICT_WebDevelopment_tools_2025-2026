@app.post("/transactions")
def create_tx(tx: Transaction, session: Session = Depends(get_session)):
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


@app.get("/transactions")
def get_tx(session: Session = Depends(get_session)):
    return session.exec(select(Transaction)).all()