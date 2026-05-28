from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from db import get_session
from app.models import Tag, TagCreate, TagRead, TransactionTag, User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=List[TagRead])
def list_tags(session: Session = Depends(get_session)) -> List[Tag]:
    return session.exec(select(Tag)).all()


@router.post("/", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag: TagCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Tag:
    tag_obj = Tag(name=tag.name)
    session.add(tag_obj)
    session.commit()
    session.refresh(tag_obj)
    return tag_obj


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тег не найден")
    session.delete(tag)
    session.commit()


# Many-to-many: добавить тег к транзакции
@router.post("/transaction/{transaction_id}/tag/{tag_id}", status_code=status.HTTP_201_CREATED)
def add_tag_to_transaction(
    transaction_id: int,
    tag_id: int,
    note: str = "",
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict:
    link = TransactionTag(transaction_id=transaction_id, tag_id=tag_id, note=note)
    session.add(link)
    session.commit()
    return {"ok": True}


@router.delete("/transaction/{transaction_id}/tag/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag_from_transaction(
    transaction_id: int,
    tag_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    link = session.exec(
        select(TransactionTag).where(
            TransactionTag.transaction_id == transaction_id,
            TransactionTag.tag_id == tag_id,
        )
    ).first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Связь не найдена")
    session.delete(link)
    session.commit()