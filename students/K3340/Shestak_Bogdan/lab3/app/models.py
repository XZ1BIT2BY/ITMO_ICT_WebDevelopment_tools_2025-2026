from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str

class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: float
    user_id: int = Field(foreign_key="user.id")


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    account_id: int = Field(foreign_key="account.id")
    category_id: int = Field(foreign_key="category.id")


class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str


class TransactionTag(SQLModel, table=True):
    transaction_id: Optional[int] = Field(
        default=None, foreign_key="transaction.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="tag.id", primary_key=True
    )

    note: str 

class UserCreate(SQLModel):
    username: str
    email: str
    password: str

class UserRead(SQLModel):
    id: int
    username: str
    email: str

class UserChangePassword(SQLModel):
    old_password: str
    new_password: str

class AccountCreate(SQLModel):
    name: str
    balance: float

class AccountRead(SQLModel):
    id: int
    name: str
    balance: float
    user_id: int

class CategoryCreate(SQLModel):
    name: str

class CategoryRead(SQLModel):
    id: int
    name: str

class TransactionCreate(SQLModel):
    amount: float
    account_id: int
    category_id: int

class TransactionRead(SQLModel):
    id: int
    amount: float
    account_id: int
    category_id: int
    category_name: str = "none"
    tag_name: str = "none"

class TagCreate(SQLModel):
    name: str

class TagRead(SQLModel):
    id: int
    name: str

class TransactionTagRead(SQLModel):
    transaction_id: int
    transaction_title: str
    tag_id: int
    tag_name: str