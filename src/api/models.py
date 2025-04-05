from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    created_at: Optional[datetime] = None

class Product(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    description: str
    stock: int

class Order(BaseModel):
    id: Optional[int] = None
    user_id: int
    product_id: int
    quantity: int
    total_price: float
    status: str
    created_at: Optional[datetime] = None
