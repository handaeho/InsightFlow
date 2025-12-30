"""
DB 연결 상태 확인 엔드포인트
    - MariaDB, MongoDB, Redis
"""

from fastapi import APIRouter
from sqlalchemy import text
from app.db.session import engine, mongo_client, redis_client

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, bool | str]:
    """
    DB 연결 상태 확인
    """
    status = {"mariadb": False, "mongodb": False, "redis": False}

    # 1. MariaDB (AsyncEngine)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status["mariadb"] = True
    except Exception as e:
        status["mariadb"] = str(e)

    # 2. MongoDB (motor 기준)
    try:
        await mongo_client.admin.command("ping")
        status["mongodb"] = True
    except Exception as e:
        status["mongodb"] = str(e)

    # 3. Redis (redis.asyncio 기준)
    try:
        await redis_client.ping()
        status["redis"] = True
    except Exception as e:
        status["redis"] = str(e)

    return status
