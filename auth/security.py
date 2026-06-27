"""Authentication helpers: password hashing and JWT tokens.

- Passwords are hashed with bcrypt and never stored in plain text.
- On login we issue a signed JWT token; the client sends it back on every
  request, and `get_current_user` verifies it and loads the matching user.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

import config
from db.database import get_db
from db.models import User

# Tells FastAPI where clients obtain a token (used by the /docs "Authorize" button).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# bcrypt only handles the first 72 bytes of a password, so we truncate to that.
_BCRYPT_MAX_BYTES = 72


def hash_password(plain_password):
    # Turn a raw password into a secure bcrypt hash for storage.
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password, hashed_password):
    # Check a raw password against the stored hash.
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(user_id):
    # Build a signed JWT that proves who the user is, valid for a limited time.
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def get_current_user(token=Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # FastAPI dependency: verify the token and return the logged-in User.
    # Any problem (missing/expired/invalid token, unknown user) -> 401.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user
