# serializers/user.py

from pydantic import BaseModel, field_validator
from typing import Literal

# Only these two roles are selectable at public registration.
# "admin" is intentionally excluded — admins are created manually.
RegisterableRole = Literal["user", "owner"]

class UserRegistrationSchema(BaseModel):
    username: str
    email: str
    password: str
    role: RegisterableRole = "user"   # defaults to customer if not provided

class UserLoginSchema(BaseModel):
    username: str
    password: str

# Response Schemas
class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        orm_mode = True

class UserTokenSchema(BaseModel):
    token: str
    message: str
    role: str   # frontend uses this right after login/register to redirect correctly