# Copyright 2025 HouHackathon-CQP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Optional, Any, Dict
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
# 1. THÊM get_current_active_user
from app.api.deps import get_current_admin, get_current_active_user 
from app.db.session import get_db
from app.core.config import settings
from app.models.enums import LocationType

router = APIRouter(prefix="/locations", tags=["locations"])

# --- CẤU HÌNH ORION ---
ORION_BASE_URL = f"{settings.orion_broker_url}/ngsi-ld/v1/entities"
ORION_UPSERT_URL = f"{settings.orion_broker_url}/ngsi-ld/v1/entityOperations/upsert?options=update"
CONTEXT = settings.ngsi_context_transportation
HEADERS = {"Content-Type": "application/ld+json", "Accept": "application/json"}

# --- HELPER: Đồng bộ sang Orion ---
async def push_location_to_orion(location_obj: models.GreenLocation):
    loc_data = schemas.LocationRead.model_validate(location_obj)
    entity_id = f"urn:ngsi-ld:{loc_data.location_type.value}:{loc_data.id}"
    
    payload = {
        "id": entity_id,
        "type": loc_data.location_type.value,
        "name": {"type": "Property", "value": loc_data.name},
        "location": {
            "type": "GeoProperty",
            "value": {"type": "Point", "coordinates": [loc_data.longitude, loc_data.latitude]}
        },
        "source": {"type": "Property", "value": "Admin Created"},
        "@context": CONTEXT
    }
    
    if loc_data.description:
        payload["description"] = {"type": "Property", "value": loc_data.description}

    async with httpx.AsyncClient() as client:
        try:
            await client.post(ORION_UPSERT_URL, json=[payload], headers=HEADERS)
            print(f"✅ Đã đồng bộ {entity_id} sang Orion")
        except Exception as e:
            print(f"❌ Lỗi Orion Upsert: {e}")

async def delete_location_from_orion(location_type: str, location_id: int):
    entity_id = f"urn:ngsi-ld:{location_type}:{location_id}"
    url = f"{ORION_BASE_URL}/{entity_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            await client.delete(url, headers=HEADERS)
            print(f"🗑️ Đã xóa {entity_id} khỏi Orion")
        except Exception as e:
            print(f"❌ Lỗi Orion Delete: {e}")

# --- API ENDPOINTS ---

@router.post("", response_model=schemas.LocationRead)
async def create_new_location(
    location: schemas.LocationCreate,
    db: AsyncSession = Depends(get_db),
    # 2. ĐỔI DEPENDENCY: Cho phép Manager truy cập
    current_user: models.User = Depends(get_current_active_user),
):
    """Tạo địa điểm mới (Admin & Manager)"""
    # 3. CHECK QUYỀN
    if current_user.role not in [models.UserRole.ADMIN, models.UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Không đủ quyền thực hiện")

    # 1. Lưu Postgres
    db_location = await crud.create_location(db=db, location=location)
    # 2. Đồng bộ Orion
    await push_location_to_orion(db_location)
    return db_location

@router.get("/{location_id}", response_model=schemas.LocationRead)
async def read_location_detail(
    location_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Lấy chi tiết (để Admin/Manager sửa) - Lấy từ Postgres"""
    location = await crud.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.put("/{location_id}", response_model=schemas.LocationRead)
async def update_location(
    location_id: int,
    location_in: schemas.LocationUpdate,
    db: AsyncSession = Depends(get_db),
    # 2. ĐỔI DEPENDENCY: Cho phép Manager truy cập
    current_user: models.User = Depends(get_current_active_user),
):
    """Cập nhật địa điểm -> Đồng bộ sang Orion (Admin & Manager)"""
    # 3. CHECK QUYỀN
    if current_user.role not in [models.UserRole.ADMIN, models.UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Không đủ quyền thực hiện")

    location = await crud.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Update DB
    updated_location = await crud.update_location(db, db_obj=location, obj_in=location_in)
    
    # Update Orion
    await push_location_to_orion(updated_location)
    
    return updated_location

@router.delete("/{location_id}")
async def delete_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    # 2. ĐỔI DEPENDENCY: Cho phép Manager truy cập
    current_user: models.User = Depends(get_current_active_user),
):
    """Xóa địa điểm -> Xóa khỏi Orion (Admin & Manager)"""
    # 3. CHECK QUYỀN
    if current_user.role not in [models.UserRole.ADMIN, models.UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Không đủ quyền thực hiện")

    location = await crud.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    loc_type = location.location_type.value
    
    # Delete DB
    await crud.delete_location(db, location_id)
    
    # Delete Orion
    await delete_location_from_orion(loc_type, location_id)
    
    return {"message": "Location deleted successfully"}

@router.get("")
async def read_all_locations(
    location_type: Optional[LocationType] = None,
    limit: int = Query(100, ge=1),
    skip: int = Query(0, ge=0),
    options: str = "keyValues",
    raw: bool = Query(False, description="True: Trả về chuẩn NGSI-LD. False: Trả về định dạng CMS.")
) -> List[Dict[str, Any]]:
    """
    Lấy danh sách địa điểm từ Orion-LD.
    Public Access (hoặc có thể thêm dependency nếu muốn chặn người ngoài)
    """
    
    params = {
        "limit": limit,
        "offset": skip,
        "options": options 
    }

    if location_type:
        params["type"] = location_type.value

    # Dùng Context Giao thông để Orion tự động rút gọn key
    read_headers = {
        "Accept": "application/ld+json",
        "Link": f'<{settings.ngsi_context_transportation}>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"'
    }

    async with httpx.AsyncClient() as client:
        try:
            # Gọi sang Orion
            response = await client.get(ORION_BASE_URL, params=params, headers=read_headers)
            
            if response.status_code == 404: 
                return []
            
            response.raise_for_status()
            data = response.json()
            
            # === TRƯỜNG HỢP 1: BÊN THỨ 3 (RAW DATA) ===
            if raw:
                return data

            # === TRƯỜNG HỢP 2: ADMIN DASHBOARD (PROCESSED DATA) ===
            for item in data:
                # 1. Làm sạch Key
                if "https://smartdatamodels.org/name" in item:
                    item["name"] = item.pop("https://smartdatamodels.org/name")
                if "https://smartdatamodels.org/source" in item:
                    item["data_source"] = item.pop("https://smartdatamodels.org/source")
                if "https://smartdatamodels.org/description" in item:
                    item["description"] = item.pop("https://smartdatamodels.org/description")

                # 2. Xử lý ID
                orion_id = item.get("id", "")
                parts = orion_id.split(":")
                
                if parts and parts[-1].isdigit():
                    item["db_id"] = int(parts[-1])
                    item["is_editable"] = True
                else:
                    item["db_id"] = None
                    item["is_editable"] = False
            
            return data

        except Exception as e:
            print(f"Error fetching locations: {e}")
            raise HTTPException(status_code=500, detail=f"Orion Error: {str(e)}")