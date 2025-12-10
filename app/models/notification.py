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

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class NotificationToken(Base):
    __tablename__ = "notification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(512), unique=True, nullable=False, index=True)
    platform = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", backref="notification_tokens")


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(Text, nullable=True)  # JSON string
    notification_type = Column(String(50), nullable=False, index=True)  # "token", "topic", "broadcast"
    topic = Column(String(255), nullable=True)  # For topic notifications
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # For user-specific notifications
    sent_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    sent_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="sent", nullable=False)  # "sent", "failed", "partial"
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    target_user = relationship("User", foreign_keys=[target_user_id], backref="received_notifications")
    sent_by_user = relationship("User", foreign_keys=[sent_by_user_id], backref="sent_notifications")
