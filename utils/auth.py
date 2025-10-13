import os
import jwt
from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from datetime import datetime, timedelta
from bson import ObjectId
from config import get_user_collection

SECRET_KEY = os.getenv("JWT_SECRET")
security = HTTPBearer()
ALGORITHM = "HS256"


def create_access_token(user_id:str):
    expire = datetime.utcnow() + timedelta(days=1)
    payload = {
        "sub":str(user_id),
        "exp":expire
    }
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)


def verify_token(token:str):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload["sub"]
    
    except jwt.ExpiredSignatureError:
        HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token has expired"
        )
    
    except jwt.InvalidSignatureError:
        HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token is invalid"
        )
    
async def get_current_user(credentials:HTTPAuthorizationCredentials = Depends(security)):
    user_id = verify_token(credentials.credentials)
    user = await get_user_collection().find_one({"_id":ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found or unverified"
        )
    return user