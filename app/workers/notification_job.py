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
from datetime import datetime, timedelta

from app import crud
from app.core.config import settings
from app.db.session import AsyncSessionLocal, init_db
from app.services import push

logger = logging.getLogger(__name__)


def _seconds_until(hour: int, minute: int) -> float:
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    return max((target - now).total_seconds(), 60.0)


async def _load_active_tokens():
    async with AsyncSessionLocal() as db:
        return await crud.get_active_tokens(db)


async def _update_after_send(token_ids: list[int], invalid_tokens: list[str]):
    async with AsyncSessionLocal() as db:
        if token_ids:
            await crud.mark_tokens_sent(db, token_ids)
        if invalid_tokens:
            await crud.deactivate_tokens_by_value(db, invalid_tokens)


async def run_daily_notification_job():
    await init_db()
    logger.info(
        "Khởi động job gửi thông báo hằng ngày (thời gian gửi %02d:%02d)",
        settings.daily_push_hour,
        settings.daily_push_minute,
    )

    while True:
        wait_seconds = _seconds_until(settings.daily_push_hour, settings.daily_push_minute)
        logger.info("Chờ %.0f giây tới lần gửi tiếp theo", wait_seconds)
        await asyncio.sleep(wait_seconds)

        try:
            tokens = await _load_active_tokens()
            token_values = [item.token for item in tokens if item.token]

            if not token_values:
                logger.info("Không có device token nào, bỏ qua lần gửi này.")
                continue

            result = await push.send_push_to_tokens(
                tokens=token_values,
                title=settings.daily_push_title,
                body=settings.daily_push_body,
            )

            invalid_tokens = result.get("invalid_tokens", [])
            sent_ids = [item.id for item in tokens if item.token not in invalid_tokens]
            await _update_after_send(sent_ids, invalid_tokens)

            logger.info(
                "Đã gửi thông báo hằng ngày: success=%s, failure=%s, invalid=%s",
                result.get("success", 0),
                result.get("failure", 0),
                len(invalid_tokens),
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Gửi thông báo hằng ngày thất bại: %s", exc)
            await asyncio.sleep(60)
