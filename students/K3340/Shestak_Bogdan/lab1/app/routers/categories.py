from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from db import get_session
from app.models import Category, User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=List[Category])
def list_categories(session: Session = Depends(get_session)) -> List[Category]:
    return session.exec(select(Category)).all()


@router.get("/{category_id}", response_model=Category)
def get_category(category_id: int, session: Session = Depends(get_session)) -> Category:
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")
    return category


@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    category: Category,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Category:
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.patch("/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    data: Category,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Category:
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)

    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")
    session.delete(category)
    session.commit()