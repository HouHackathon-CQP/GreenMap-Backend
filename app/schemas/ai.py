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

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AIReportBase(BaseModel):
    lat: float
    lon: float
    provider: str
    model: str | None = None
    analysis: str
    context: dict[str, Any] | None = None


class AIReportRead(AIReportBase):
    id: int
    user_id: int | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
