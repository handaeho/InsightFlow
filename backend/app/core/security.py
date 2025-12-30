"""
보안 관련 유틸리티 설정
    - 비밀번호 해싱(bcrypt), JWT 인코딩/디코딩
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings


# 비밀번호 해싱 컨택스트 (Bcrypt 암호화 적용)
passwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto"
)  # deprecated: 암호화 알고리즘 변경 시, 기존 패스워드 자동 업데이트 적용


def create_access_token(subject: Union[str, Any]) -> str:
    """
    액세스 토큰 생성
    """
    # None 타입 방어
    if subject is None:
        return ""

    # 1. 만료 시간 설정
    expire_time = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # 2. payload 구성 (subject: 사용자 ID, expire_time: 토큰 만료 시간)
    payload = {"sub": str(subject), "exp": expire_time}

    # 3. jwt.encode()로 서명 및 토큰 생성 (payload에 SECRET_KEY 적용)
    algorithm = getattr(settings, "ALGORITHM", "HS256")
    access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=algorithm)

    return access_token


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증

    plain_password: 사용자 입력 평문 패스워드
    hashed_password: DB 저장 암호화 패스워드
    """
    # 평문에 Bcrypt 알고리즘으로 해싱 후, DB 값과 비교
    return passwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호 해싱
    """
    # 사용자 입력 평문 패스워드를 난수 문자열(해시)로 변환
    return passwd_context.hash(password)
