from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas import RefreshInput, SigninInput, TokenPair
from app.services.auth import refresh as refresh_tokens
from app.services.auth import signin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signin", response_model=TokenPair)
async def signin_route(payload: SigninInput, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        return await signin(session, payload.email, payload.password, payload.device_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/refresh", response_model=TokenPair)
async def refresh_route(payload: RefreshInput, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    try:
        return await refresh_tokens(session, payload.user_id, payload.device_id, payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
