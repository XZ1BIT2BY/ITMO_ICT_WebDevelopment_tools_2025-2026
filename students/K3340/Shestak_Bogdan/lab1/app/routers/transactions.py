from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from db import get_session
from app.models import (
    Transaction,
    TransactionCreate,
    TransactionRead,
    Account,
    User,
    Category,
    Tag,
    TransactionTag,
    TransactionTagRead,
)
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _check_owner(account_id: int, user_id: int, session: Session) -> Account:
    account = session.get(Account, account_id)
    if not account or account.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Счёт не найден")
    return account


def _get_transaction_tag_name(transaction_id: int, session: Session) -> str:
    tag_name = session.exec(
        select(Tag.name)
        .join(TransactionTag, TransactionTag.tag_id == Tag.id)
        .where(TransactionTag.transaction_id == transaction_id)
    ).first()
    return tag_name or "none"


def _get_transaction_category_name(category_id: int, session: Session) -> str:
    category = session.get(Category, category_id)
    return category.name if category else "none"


@router.get("/", response_model=List[TransactionRead])
def list_transactions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[TransactionRead]:
    accounts = session.exec(select(Account).where(Account.user_id == current_user.id)).all()
    account_ids = [a.id for a in accounts]
    transactions = session.exec(
        select(Transaction).where(Transaction.account_id.in_(account_ids))
    ).all()

    return [
        TransactionRead(
            id=tx.id,
            amount=tx.amount,
            account_id=tx.account_id,
            category_id=tx.category_id,
            category_name=_get_transaction_category_name(tx.category_id, session),
            tag_name=_get_transaction_tag_name(tx.id, session),
        )
        for tx in transactions
    ]


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionRead:
    tx = session.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Транзакция не найдена")
    _check_owner(tx.account_id, current_user.id, session)
    return TransactionRead(
        id=tx.id,
        amount=tx.amount,
        account_id=tx.account_id,
        category_id=tx.category_id,
        category_name=_get_transaction_category_name(tx.category_id, session),
        tag_name=_get_transaction_tag_name(tx.id, session),
    )


@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx: TransactionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionRead:
    _check_owner(tx.account_id, current_user.id, session)
    tx_obj = Transaction(amount=tx.amount, account_id=tx.account_id, category_id=tx.category_id)
    session.add(tx_obj)
    session.commit()
    session.refresh(tx_obj)
    return TransactionRead(
        id=tx_obj.id,
        amount=tx_obj.amount,
        account_id=tx_obj.account_id,
        category_id=tx_obj.category_id,
        category_name=_get_transaction_category_name(tx_obj.category_id, session),
        tag_name=_get_transaction_tag_name(tx_obj.id, session),
    )


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    data: TransactionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TransactionRead:
    tx = session.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Транзакция не найдена")
    _check_owner(tx.account_id, current_user.id, session)

    tx.amount = data.amount
    tx.account_id = data.account_id
    tx.category_id = data.category_id
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return TransactionRead(
        id=tx.id,
        amount=tx.amount,
        account_id=tx.account_id,
        category_id=tx.category_id,
        category_name=_get_transaction_category_name(tx.category_id, session),
        tag_name=_get_transaction_tag_name(tx.id, session),
    )


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


@router.get("/{transaction_id}/tags", response_model=List[TransactionTagRead])
def get_transaction_tags(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[TransactionTagRead]:
    tx = session.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Транзакция не найдена")
    _check_owner(tx.account_id, current_user.id, session)

    rows = session.exec(
        select(TransactionTag, Tag)
        .join(Tag, TransactionTag.tag_id == Tag.id)
        .where(TransactionTag.transaction_id == transaction_id)
    ).all()

    return [
        TransactionTagRead(
            transaction_id=link.transaction_id,
            transaction_title=link.note,
            tag_id=tag.id,
            tag_name=tag.name,
        )
        for link, tag in rows
    ]