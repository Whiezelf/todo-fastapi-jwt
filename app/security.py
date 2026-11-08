import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt

# Nessun valore di default: se SECRET_KEY manca, l'app non parte.
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

import hashlib
import secrets

RESET_TOKEN_EXPIRE_MINUTES = 30


def generate_reset_token() -> tuple[str, str, datetime]:
    """Genera un token casuale ad alta entropia. Restituiamo sia il token
    in chiaro (va nell'email, mai salvato) sia il suo hash (va nel
    database): così, anche se il database venisse letto da qualcuno,
    non potrebbe usare i token per resettare password altrui."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    return raw_token, token_hash, expires_at


def hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()
