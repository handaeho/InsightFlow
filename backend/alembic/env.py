"""
Alembic: Database Migration Tool
    - SQLAlchemy 기반의 데이터베이스 마이그레이션 도구
    - 데이터베이스 스키마를 버전 관리하고, 애플리케이션의 변경 사항에 따라 데이터베이스를 업데이트
    - SQLAIchemy 모델 정보의 변경을 자동적으로 인식하여 migraion 파일을 생성
    - Alembic 초기화 후, 자동 생성된 env.py 수정
        - 기존 동기 방식의 Alembic을 비동기 환경으로 전환
        - FastAPI + SQLAlchemy 비동기(Async) 환경 호환 커스터마이즈 설정
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool  # DB 연결 Pool
from sqlalchemy.engine import Connection  # DB 연결 객체 타입 힌트
from sqlalchemy.ext.asyncio import async_engine_from_config  # 비동기 엔진 생성

from alembic import context  # Alembic 마이그레이션 설정

# 프로젝트의 설정 및 모델
# 모델들을 여기서 import 해줘야 Alembic이 테이블을 인식함
from app.core.config import settings
from app.db.models.base import Base
from app.db.models.users import User
from app.db.models.files import File

# alembic.ini
config = context.config

# 로깅 레벨 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic이 프로젝트에서 생성한 테이블을 인식
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    오프라인 모드
        - DB에 직접 연결하지 않고, 실행될 SQL 쿼리문만 파일로 생성
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    온라인 모드
        - 동기(Sync) 방식의 run_migrations 함수를 비동기로 실행하기 위해 래핑
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    온라인 모드
        - 비동기 DB 드라이버(asyncmy)를 사용하여 실제 DB에 마이그레이션을 적용
    """

    # config.py의 설정값으로 DB URL을 덮어씀
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = (
        # 비동기용 드라이버(asyncmy) 지정
        f"mysql+asyncmy://{settings.MARIADB_USER}:{settings.MARIADB_PASSWORD}"
        f"@{settings.MARIADB_SERVER}:{settings.MARIADB_PORT}/{settings.MARIADB_DB}"
    )

    # 비동기 엔진 생성
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # 연결을 재사용하지 않음 (마이그레이션 후, 연결 종료)
    )

    # 비동기적으로 DB에 연결
    async with connectable.connect() as connection:
        # 비동기 연결(connection) 위에서 동기 함수인 do_run_migrations를 실행
        # 비동기 환경에서 Alembic을 돌리는 표준 패턴
        await connection.run_sync(do_run_migrations)

    # 작업 종료 후, 엔진 종료
    await connectable.dispose()


# Alembic 실행 모드 확인 (오프라인/온라인)
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
