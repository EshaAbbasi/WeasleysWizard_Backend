# serializers/shop.py

from pydantic import BaseModel
from typing import Optional, Literal

class ShopCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None

class ShopUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ShopAuthorizeSchema(BaseModel):
    is_authorized: bool = True

class ShopSchema(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str] = None
    status: str
    is_authorized: bool

    class Config:
     from_attributes = True
class AdminShopSchema(ShopSchema):
    owner_username: str

class ShopStatusUpdateSchema(BaseModel):
    # Admin uses this to approve or suspend — reusing one route for both
    status: Literal['approved', 'suspended', 'pending']