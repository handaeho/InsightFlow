"""
File 테이블 정의
"""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.models.base import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(
        # PK, index 설정(검색 용이)
        primary_key=True,
        index=True,
    )

    filename: Mapped[str] = mapped_column(String(255), index=True)
    saved_path: Mapped[str] = mapped_column(String(512))  # 로컬 디스크 저장 경로
    file_size: Mapped[int] = mapped_column(Integer)  # 바이트 단위 크기

    # NOTE: 추후 User 테이블과 ForeignKey로 연결할 수 있음 (일단은 단순화)
    # uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(
        # 데이터가 INSERT 되는 순간, DB 서버의 현재 시간(NOW())을 자동으로 입력
        DateTime(timezone=True),
        server_default=func.now(),
    )
