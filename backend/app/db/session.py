"""
DB 연결 객체 생성
    - 비동기(Async) 방식 사용
    - config.py에 정의한 설정값(settings) 사용
"""

from typing import Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from app.core.config import settings

# ---------- RDB ----------
DATABASE_URL = (
    # 비동기 전용 드라이버 사용 명시 (기존 "mysql://"는 동기 방식)
    f"mysql+asyncmy://{settings.MARIADB_USER}:{settings.MARIADB_PASSWORD}"
    f"@{settings.MARIADB_SERVER}:{settings.MARIADB_PORT}/{settings.MARIADB_DB}"
)

# 데이터베이스 연결 풀 생성 (SQLAlchemy 2.0의 비동기 기능 활용)
engine = create_async_engine(
    DATABASE_URL, echo=True
)  # echo: SQL 쿼리 출력 (운영 환경 False 권장)

# DB 트랜잭션 수행 객체 (API 요청 시, 호출해 세션 추출)
AsyncSessionLocal = async_sessionmaker[AsyncSession](
    bind=engine,
    expire_on_commit=False,  # 비동기 처리를 위해, 커밋 후에도 데이터 만료 금지
)

# ---------- MongoDB ----------
mongo_client = AsyncIOMotorClient[Any](
    f"mongodb://{settings.MONGODB_USER}:{settings.MONGODB_PASSWORD}"
    f"@{settings.MONGODB_SERVER}:{settings.MONGODB_PORT}/?authSource=admin"
)

# ---------- Redis ----------
redis_client = Redis.from_url(
    f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_SERVER}:{settings.REDIS_PORT}/0",
    decode_responses=True,  # redis 값 조회 시, 원본 바이트 타입을 문자열로 자동 디코딩
)
