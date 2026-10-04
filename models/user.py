from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from config.environment import JWT_SECRET

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserModel(BaseModel):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)  # Each username must be unique
    email = Column(String, unique=True)  # Each email must be unique
    password = Column(String, nullable=True)
    role= Column(Enum('user', 'admin','owner', name='user_roles'), default='user')  # Role can be 'user', 'admin', or 'owner'
    def set_password(self, plain_txt_password: str):
        if not plain_txt_password:
            raise ValueError("Password cannot be empty")
        self.password = pwd_context.hash(plain_txt_password)

    def verify_password(self, plain_txt_password: str) -> bool:
        if not plain_txt_password or not self.password:
            return False
        return pwd_context.verify(plain_txt_password, self.password)

    def generate_token(self):
        payload = {
        "exp": datetime.now(timezone.utc) + timedelta(days=1),  # Expiration time (1 day)
        "iat": datetime.now(timezone.utc),  # Issued at time
        "sub": str(self.id),  # Subject - the user ID
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        return token