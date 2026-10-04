# dependencies/get_current_user.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models.user import UserModel
from database import get_db
import jwt
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError
from jwt.exceptions import InvalidSubjectError
from config.environment import JWT_SECRET

# FastAPI helper to extract the token from the auth header: "Bearer ...."
http_bearer = HTTPBearer()

def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer)
) -> UserModel:
    try:
        # Decode the token using the secret key
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        current_user_id = payload.get("sub")

        if current_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token missing subject"
            )

        # "sub" is stored as a string in the token (see UserModel.generate_token),
        # so cast it back to int before querying — UserModel.id is an Integer column.
        user = db.query(UserModel).filter(UserModel.id == int(current_user_id)).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists"
            )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token has expired"
        )

    except InvalidSubjectError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token subject is invalid"
        )

    except DecodeError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not decode token: {str(err)}"
        )

    except InvalidTokenError as err:
        # Catch-all for any other PyJWT error (e.g. malformed token)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid token: {str(err)}"
        )

    return user