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

import asyncio
import logging
from pathlib import Path
from typing import Iterable

import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

logger = logging.getLogger(__name__)
# firebase-admin >=7 removed send_multicast; keep compatibility with both APIs.
_multicast_sender = getattr(messaging, "send_multicast", None) or messaging.send_each_for_multicast

_firebase_app: firebase_admin.App | None = None


def _init_firebase_app() -> firebase_admin.App:
    global _firebase_app  # pylint: disable=global-statement
    if _firebase_app:
        return _firebase_app

    cred_path = settings.firebase_credentials_file
    if not cred_path:
        raise RuntimeError("Thiếu cấu hình FIREBASE_CREDENTIALS_FILE trong .env")

    path_obj = Path(cred_path)
    if not path_obj.exists():
        raise RuntimeError(f"Tệp khóa dịch vụ Firebase không tồn tại: {cred_path}")

    cred = credentials.Certificate(cred_path)
    _firebase_app = firebase_admin.initialize_app(cred)
    logger.info("Đã khởi tạo Firebase Admin SDK cho FCM")
    return _firebase_app


async def send_push_to_tokens(
    tokens: Iterable[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Gửi push notification đến danh sách registration tokens.
    Trả về dict gồm số lần gửi thành công/thất bại và danh sách token không còn hợp lệ.
    """
    token_list = [t for t in tokens if t]
    if not token_list:
        return {"success": 0, "failure": 0, "invalid_tokens": []}

    app_instance = _init_firebase_app()
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=token_list,
        data={k: str(v) for k, v in (data or {}).items()},
    )

    response = await asyncio.to_thread(
        _multicast_sender, message, app=app_instance, dry_run=dry_run
    )

    invalid_tokens: list[str] = []
    errors: list[dict[str, str]] = []
    for idx, resp in enumerate(response.responses):
        if resp.success:
            continue
        code = getattr(resp.exception, "code", "") if resp.exception else ""
        code_lower = str(code).lower()
        code_norm = code_lower.replace("_", "-")
        msg = (
            getattr(resp.exception, "message", "")
            or str(resp.exception) if resp.exception else ""
        )
        token = token_list[idx] if idx < len(token_list) else ""
        errors.append({"token": token, "code": code, "message": msg})
        logger.warning("FCM send fail token=%s code=%s msg=%s", token, code, msg)
        if code_norm in {"registration-token-not-registered", "invalid-argument"}:
            invalid_tokens.append(token_list[idx])

    return {
        "success": response.success_count,
        "failure": response.failure_count,
        "invalid_tokens": invalid_tokens,
        "errors": errors,
    }


async def send_topic_notification(
    topic: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Gửi push notification tới một topic (nếu mobile app subscribe).
    """
    app_instance = _init_firebase_app()
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        topic=topic,
        data={k: str(v) for k, v in (data or {}).items()},
    )
    response_id = await asyncio.to_thread(
        messaging.send, message, app=app_instance, dry_run=dry_run
    )
    return {"message_id": response_id}
