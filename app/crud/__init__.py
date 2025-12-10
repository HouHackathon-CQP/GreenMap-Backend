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

from app.crud.location import create_location, get_locations, get_location, update_location, delete_location
from app.crud.report import create_report, get_reports, update_report_status
from app.crud.user import create_user, get_user_by_email, get_user_by_id, get_all_users, update_user, delete_user, change_password
from app.crud.notification import (
    upsert_device_token,
    deactivate_token,
    deactivate_tokens_by_value,
    get_active_tokens,
    get_all_tokens,
    mark_tokens_sent,
    create_notification_history,
    get_notification_history,
    get_notification_history_by_id,
    delete_old_notification_history,
)
from app.crud.ai_report import create_ai_report, list_ai_reports, get_ai_report

__all__ = [
    "create_location",
    "get_locations",
    "get_location",
    "update_location",
    "delete_location",
    "create_report",
    "get_reports",
    "update_report_status",
    "create_user",
    "get_user_by_email",
    "get_user_by_id",
    "get_all_users",
    "update_user",
    "delete_user",
    "change_password",
    "upsert_device_token",
    "deactivate_token",
    "deactivate_tokens_by_value",
    "get_active_tokens",
    "get_all_tokens",
    "mark_tokens_sent",
    "create_notification_history",
    "get_notification_history",
    "get_notification_history_by_id",
    "delete_old_notification_history",
    "create_ai_report",
    "list_ai_reports",
    "get_ai_report",
]
