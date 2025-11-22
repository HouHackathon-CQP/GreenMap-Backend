from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api.deps import get_current_admin
from app.db.session import get_db

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("", response_model=schemas.LocationRead)
async def create_new_location(
    location: schemas.LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_admin),
):
    return await crud.create_location(db=db, location=location)


@router.get("", response_model=List[schemas.LocationRead])
async def read_all_locations(
    location_type: Optional[models.LocationType] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_locations(
        db=db, location_type=location_type, skip=skip, limit=limit
    )
