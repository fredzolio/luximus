import jwt
import datetime
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("SECRET_KEY_TOKEN_STATE")
JWT_ALGORITHM = "HS256"

def generate_state(user_id: str, expires_in: int = 300) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def get_user_id_from_state(state: str) -> Optional[str]:
    try:
        payload = jwt.decode(state, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        return user_id
    except jwt.ExpiredSignatureError:
        print("State token has expired.")
        return None
    except jwt.InvalidTokenError:
        print("Invalid state token.")
        return None
