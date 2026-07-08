from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import os
from uuid import uuid4

from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RefreshToken, User

SECRET = "defectrail-local-secret"
ITERATIONS = 120_000


async def ensure_demo_user(session: AsyncSession) -> User:
    user = await session.scalar(select(User).where(User.email == "operator@defectrail.local"))
    if user:
        return user

    user = User(
        email="operator@defectrail.local",
        phone="+821012345678",
        password_hash=hash_secret("defectrail"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def signin(session: AsyncSession, email: str, password: str, device_id: str) -> dict[str, str]:
    user = await session.scalar(select(User).where(User.email == email))
    if not user or not verify_secret(password, user.password_hash):
        raise ValueError("invalid credentials")
    return await issue_tokens(session, user, device_id)


async def refresh(session: AsyncSession, user_id: str, device_id: str, refresh_token: str) -> dict[str, str]:
    saved = await session.scalar(
        select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.device_id == device_id)
    )
    if not saved or saved.refresh_token_exp <= datetime.now(UTC).replace(tzinfo=None):
        raise ValueError("invalid refresh token")
    if not verify_secret(refresh_token, saved.refresh_token_hash):
        raise ValueError("invalid refresh token")
    user = await session.get(User, user_id)
    if not user:
        raise ValueError("invalid refresh token")
    return await issue_tokens(session, user, device_id)


async def issue_tokens(session: AsyncSession, user: User, device_id: str) -> dict[str, str]:
    now = datetime.now(UTC)
    access_token = jwt.encode({"sub": user.user_id, "exp": now + timedelta(minutes=15)}, SECRET, algorithm="HS256")
    refresh_token = jwt.encode(
        {"sub": user.user_id, "deviceId": device_id, "jti": str(uuid4()), "exp": now + timedelta(days=7)},
        SECRET,
        algorithm="HS256",
    )
    refresh_exp = now + timedelta(days=7)
    saved = await session.scalar(
        select(RefreshToken).where(RefreshToken.user_id == user.user_id, RefreshToken.device_id == device_id)
    )
    if saved:
        saved.refresh_token_hash = hash_secret(refresh_token)
        saved.refresh_token_exp = refresh_exp.replace(tzinfo=None)
        saved.updated_at = now.replace(tzinfo=None)
    else:
        session.add(
            RefreshToken(
                user_id=user.user_id,
                device_id=device_id,
                refresh_token_hash=hash_secret(refresh_token),
                refresh_token_exp=refresh_exp.replace(tzinfo=None),
            )
        )
    await session.commit()
    return {"access_token": access_token, "refresh_token": refresh_token}


def hash_secret(value: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", value.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_secret(value: str, saved: str) -> bool:
    try:
        _, iterations, salt_hex, digest_hex = saved.split("$", 3)
        digest = hashlib.pbkdf2_hmac("sha256", value.encode(), bytes.fromhex(salt_hex), int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)
