# serializers/shop.py

from pydantic import BaseModel
from typing import Optional, Literal

class ShopCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None

class ShopSchema(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str] = None
    status: str
    is_authorized: bool

    class Config:
        orm_mode = True

class ShopStatusUpdateSchema(BaseModel):
    # Admin uses this to approve or suspend — reusing one route for both
    status: Literal['approved', 'suspended', 'pending']