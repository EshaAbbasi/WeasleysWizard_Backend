# controllers/users.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import UserModel
from serializers.user import (
    UserSchema,
    UserRegistrationSchema,
    UserLoginSchema,
    UserTokenSchema,
    UserUpdateSchema,
)
from database import get_db
from dependencies.get_current_user import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserTokenSchema, status_code=201)
def create_user(user: UserRegistrationSchema, db: Session = Depends(get_db)):
    existing_user = db.query(UserModel).filter(
        (UserModel.username == user.username) | (UserModel.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    new_user = UserModel(username=user.username, email=user.email, role=user.role)
    new_user.set_password(user.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = new_user.generate_token()
    return {"token": token, "message": "Registration successful", "role": new_user.role}


@router.post("/login", response_model=UserTokenSchema, status_code=201)
def login(user: UserLoginSchema, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()

    if not db_user or not db_user.verify_password(user.password):
        raise HTTPException(status_code=409, detail="Invalid username or password")

    token = db_user.generate_token()
    return {"token": token, "message": "Login successful", "role": db_user.role}


@router.get('/current_user', response_model=UserSchema)
def current_user(user: UserModel = Depends(get_current_user)):
    return user


@router.put("/users/me", response_model=UserSchema)
def update_current_user(
    update: UserUpdateSchema,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
):
    payload = update.dict(exclude_unset=True)
    if not payload:
        return user

    new_username = payload.get("username")
    new_email = payload.get("email")

    if new_username and new_username != user.username:
        taken = db.query(UserModel).filter(UserModel.username == new_username, UserModel.id != user.id).first()
        if taken:
            raise HTTPException(status_code=409, detail="Username already exists")
        user.username = new_username

    if new_email and new_email != user.email:
        taken = db.query(UserModel).filter(UserModel.email == new_email, UserModel.id != user.id).first()
        if taken:
            raise HTTPException(status_code=409, detail="Email already exists")
        user.email = new_email

    if payload.get("password"):
        user.set_password(payload["password"])

    db.commit()
    db.refresh(user)
    return user
