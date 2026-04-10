from students.K3340.Shestak_Bogdan.practics.practic_1.models import BaseModel
from typing import List, Optional

class Transaction(BaseModel):
    id: int
    amount: float
    description: str


class Account(BaseModel):
    id: int
    name: str
    balance: float
    transactions: Optional[List[Transaction]] = []