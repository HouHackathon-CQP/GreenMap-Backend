from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=schemas.UserRead)
async def create_new_user(
    user: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
):
    db_user = await crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db=db, user=user)
