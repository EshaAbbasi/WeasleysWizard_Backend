# serializers/user.py

from pydantic import BaseModel
from typing import Literal, Optional

RegisterableRole = Literal["user", "owner"]

class UserRegistrationSchema(BaseModel):
    username: str
    email: str
    password: str
    role: RegisterableRole = "user"

class UserLoginSchema(BaseModel):
    username: str
    password: str

class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

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
    role: str