"""
토큰 검사 의존성 주입(Dependency Injection)
    - API 요청이 들어올 때마다 토큰이 유효한지 검사
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.db.session import redis_client
from app.core.config import settings

# 1. 로그인 URL (OAuth2PasswordBearer: Header의 Authorization 필드에서 "Bearer <토큰>" 값을 찾아 추출)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    사용자 검증

    Depends: 의존성 주입 (get_current_user 호출 시, 먼저 oauth2_scheme 실행)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 검증할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 토큰 블랙리스트 확인
    is_blacklisted = await redis_client.get(f"blacklist:{token}")
    if is_blacklisted:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token=token,  # 헤더의 토큰 문자열
            key=settings.SECRET_KEY,  # 비밀키 (서명 검증)
            algorithms=[settings.ALGORITHM],  # 토큰 생성 암호화 알고리즘
        )

        # payload에서 subject(사용자 식별값) 추출
        username: Optional[str] = payload.get("sub")

        # 서명은 일치하나, suject가 없을 경우
        if username is None:
            raise credentials_exception

    except JWTError:
        # 토큰 만료 또는 형식 불일치
        raise credentials_exception

    return username
