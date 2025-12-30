"""
Users 테이블 정의
"""

from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.models.base import Base


class User(Base):
    """
    Base를 상속받아 User라는 모델 생성
        - Mapped: 파이썬 타입 힌트를 통해 컬럼의 데이터 타입을 명시하는 제네릭 타입
        - mapped_column: 컬럼의 세부 설정(제약 조건, 기본값 등) 정의
    """

    # 테이블 이름 지정
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        # PK, index 설정(검색 용이)
        primary_key=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        # 중복 방지, index 설정(검색 용이)
        String(255),
        unique=True,
        index=True,
    )

    hashed_password: Mapped[str] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(default=True)  # 기본값: True(활성)

    is_superuser: Mapped[bool] = mapped_column(
        # 기본값: False(일반 사용자)
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        # 데이터가 INSERT 되는 순간, DB 서버의 현재 시간(NOW())을 자동으로 입력
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # nullable=False는 타입 힌트가 Optional이 아니면 자동 적용
    # NULL 허용: Mapped[Optional[str]] 또는 Mapped[str | None]
