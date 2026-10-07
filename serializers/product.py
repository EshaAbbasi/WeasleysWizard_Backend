# serializers/product.py

from pydantic import BaseModel
from typing import Optional, List, Literal
from decimal import Decimal

ProductCategory = Literal[
    "Trunk Station",
    "Wands",
    "Robes & Clothing",
    "Gifts",
    "Home and Accessories",
]

class ProductCreateSchema(BaseModel):
    name: str
    category: ProductCategory
    description: Optional[str] = None
    price_gbp: Decimal
    stock: int = 0
    image_urls: List[str] = []
    is_banned_at_hogwarts: bool = False

class ProductUpdateSchema(BaseModel):
    name: Optional[str] = None
    category: Optional[ProductCategory] = None
    description: Optional[str] = None
    price_gbp: Optional[Decimal] = None
    stock: Optional[int] = None
    image_urls: Optional[List[str]] = None
    is_banned_at_hogwarts: Optional[bool] = None

class ProductSchema(BaseModel):
    id: int
    shop_id: int
    category: str
    name: str
    description: Optional[str] = None
    price_gbp: Decimal
    stock: int
    image_urls: List[str]
    is_banned_at_hogwarts: bool

    class Config:
        from_attributes=True