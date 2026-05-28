from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from db import get_session
from app.models import Category, CategoryCreate, CategoryRead, User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=List[CategoryRead])
def list_categories(session: Session = Depends(get_session)) -> List[Category]:
    return session.exec(select(Category)).all()


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, session: Session = Depends(get_session)) -> Category:
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")
    return category


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Category:
    category_obj = Category(name=category.name)
    session.add(category_obj)
    session.commit()
    session.refresh(category_obj)
    return category_obj


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    data: CategoryCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Category:
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")

    category.name = data.name
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