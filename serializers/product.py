# serializers/product.py

from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class ProductCreateSchema(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    price_gbp: Decimal
    stock: int = 0
    image_urls: List[str] = []
    is_banned_at_hogwarts: bool = False

class ProductUpdateSchema(BaseModel):
    # Same fields, but all optional — partial updates allowed
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price_gbp: Optional[Decimal] = None
    stock: Optional[int] = None
    image_urls: Optional[List[str]] = None
    is_banned_at_hogwarts: Optional[bool] = None

class ProductSchema(BaseModel):
    id: int
    shop_id: int
    name: str
    category: str
    description: Optional[str] = None
    price_gbp: Decimal
    stock: int
    image_urls: List[str]
    is_banned_at_hogwarts: bool

    class Config:
        orm_mode = True