"""
사용자 인증 엔드포인트
    - ID, 패스워드를 검증하고 토큰 생성
"""

from datetime import datetime, timezone
from jose import jwt, JWTError
from typing import Any

from fastapi import status
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api import deps
from app.core.security import verify_password, create_access_token
from app.db.session import redis_client
from app.core.config import settings

router = APIRouter()

# TODO: 임시 계정 (반드시 삭제)
TEMP_ADMIN_USER = "admin"
TEMP_ADMIN_HASH = (
    "$2b$12$3/t4hczp61FgobqLqJkcMeRau35EKG1fc45IlY08e/Nw4NH9ScFt2"  # secret123
)


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    로그인

    Depends: 의존성 주입
        - login 호출 시, 먼저 OAuth2PasswordRequestForm 실행
        - OAuth2PasswordRequestForm: HTTP 요청의 본문(Body)에서 username과 password 필드 추출
    """
    # 1. ID 검증
    if form_data.username != TEMP_ADMIN_USER:
        return HTTPException(
            status_code=400, detail="사용자 ID 또는 비밀번호를 확인하세요."
        )

    # 2. 패스워드 검증
    if not verify_password(
        plain_password=form_data.password, hashed_password=TEMP_ADMIN_HASH
    ):
        raise HTTPException(
            status_code=400, detail="사용자 ID 또는 비밀번호를 확인하세요."
        )

    # 3. 토큰 발급
    return {
        "access_token": create_access_token(subject=form_data.username),
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(token: str = Depends(deps.oauth2_scheme)):
    """
    로그아웃
        - 토큰을 Redis 블랙리스트에 등록하여 무효화
    """
    try:
        # 1. 기존 토큰 만료 시간(ttl) 계산
        payload = jwt.decode(
            token=token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        exp = payload.get("exp")
        current_time = datetime.now(timezone.utc).timestamp()
        ttl = int(exp - current_time)

        # 2. Redis 블랙리스트 저장 (Key: "blacklist:토큰값", Value: "logout", TTL: 남은시간)
        if ttl > 0:  # 만료되지 않은 토큰만 블랙리스트 처리
            await redis_client.setex(f"blacklist:{token}", ttl, "logout")

        return {"msg": "성공적으로 로그아웃 했습니다."}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )


@router.get("/me")
def read_users_me(current_user: str = Depends(deps.get_current_user)):
    """
    내 정보 조회

    Depends: 의존성 주입
        - read_users_me 호출 시, 먼저 deps.get_current_user 실행
        - deps.get_current_user: 헤더 토큰 추출, 위/변조 검사, 만료 확인, username 반환
    """
    return {"username": current_user, "role": "admin"}
