from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.rate_limit import rate_limit_by_ip
from app.schemas import LoginIn, Token, UserCreate, UserOut

router = APIRouter()

_auth_rate_limit = rate_limit_by_ip("auth", count=20, window_seconds=60)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_auth_rate_limit),
):
    user = User(email=payload.email.lower(), hashed_password=hash_password(payload.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    payload: LoginIn,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_auth_rate_limit),
):
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    access_token = create_access_token(user.id)
    return Token(access_token=access_token)
