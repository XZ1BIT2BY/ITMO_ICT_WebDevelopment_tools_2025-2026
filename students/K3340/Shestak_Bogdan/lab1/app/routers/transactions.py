from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from db import get_session
from app.models import Transaction, Account, User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _check_owner(account_id: int, user_id: int, session: Session) -> Account:
    account = session.get(Account, account_id)
    if not account or account.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт не найден")
    return account


@router.get("/", response_model=List[Transaction])
def list_transactions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Transaction]:
    accounts = session.exec(select(Account).where(Account.user_id == current_user.id)).all()
    account_ids = [a.id for a in accounts]
    return session.exec(
        select(Transaction).where(Transaction.account_id.in_(account_ids))
    ).all()


@router.get("/{transaction_id}", response_model=Transaction)
def get_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    tx = session.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Транзакция не найдена")
    _check_owner(tx.account_id, current_user.id, session)
    return tx


@router.post("/", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx: Transaction,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    _check_owner(tx.account_id, current_user.id, session)
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


@router.patch("/{transaction_id}", response_model=Transaction)
def update_transaction(
    transaction_id: int,
    data: Transaction,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    tx = session.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Транзакция не найдена")
    _check_owner(tx.account_id, current_user.id, session)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tx, key, value)

    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    tx = session.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Транзакция не найдена")
    _check_owner(tx.account_id, current_user.id, session)
    session.delete(tx)
    session.commit()