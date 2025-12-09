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

from pydantic import BaseModel, ConfigDict


class DeviceTokenCreate(BaseModel):
    token: str
    platform: str | None = None


class DeviceTokenRead(BaseModel):
    id: int
    token: str
    platform: str | None = None
    is_active: bool
    user_id: int | None = None
    last_sent_at: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PushMessage(BaseModel):
    title: str
    body: str
    data: dict[str, str] | None = None
    dry_run: bool = False


class TopicPushMessage(PushMessage):
    topic: str | None = None
