from fastapi import Depends, HTTPException
from models.user import UserModel
from dependencies.get_current_user import get_current_user

def require_role(*allowed_roles: str):
    def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires one of these roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
