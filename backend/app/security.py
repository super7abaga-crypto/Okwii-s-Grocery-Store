import os

import jwt

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pwdlib import PasswordHash


load_dotenv()

SECRET_KEY = os.getenv("OGS_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("OGS_SECRET_KEY is missing from your .env file.")

ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(customer_id: int) -> str:

    expiration = datetime.now(timezone.utc) + timedelta(hours=24)

    payload = {
        "sub": str(customer_id),
        "exp": expiration
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)