from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(tags=["system"])


@router.get("/")
async def root():
    return {"message": "GreenMap Backend is Running!"}


@router.get("/test-db")
async def test_db_connection(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "Database Connected Successfully"}
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"DB Error: {exc}") from exc
