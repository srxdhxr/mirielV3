import jwt
from datetime import datetime, timedelta

from app.core.config import settings

def create_access_token(user_id, tenant_id,email):
    payload = {
        "user_id":user_id,
        "tenant_id":tenant_id,
        "email":email,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow()
    }

    #encode the payload
    token = jwt.encode(payload,settings.SECRET_KEY,algorithm=settings.JWT_ALGORITHM)

    return token

def verify_token(token):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token