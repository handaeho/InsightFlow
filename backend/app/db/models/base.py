from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    모든 모델의 최상위 부모 클래스
        - 이곳에 정의된 Base를 상속받아야 Alembic이 테이블을 인식함
    """

    pass
