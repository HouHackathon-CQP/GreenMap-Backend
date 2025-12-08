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

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from geoalchemy2 import Geometry
from app.db.session import Base

class TrafficSegment(Base):
    __tablename__ = "traffic_segments"
    
    id = Column(String, primary_key=True) # ID làn đường (ví dụ: "edge1_0")
    # Lưu hình học đoạn đường để vẽ lên bản đồ
    geom = Column(Geometry("LINESTRING", srid=4326))

class SimulationFrame(Base):
    __tablename__ = "simulation_frames"
    
    # Khóa chính phức hợp: Tại giây thứ X, đoạn đường Y có trạng thái Z
    id = Column(Integer, primary_key=True, autoincrement=True)
    time_second = Column(Integer, index=True) # Giây thứ mấy trong vòng lặp (0-3600)
    segment_id = Column(String, ForeignKey("traffic_segments.id"), index=True)
    
    avg_speed = Column(Float)
    status_color = Column(String(10)) # 'green', 'orange', 'red'