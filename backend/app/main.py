import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoint import health, auth

app = FastAPI(
    title="InsightFlow",
    description="InsightFlow is a data analysis and visualization platform that applies natural language commands to workflows.",
)

# CORS (Cross-Origin Resource Sharing) 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # TODO: 개발 중이니 모든 출처 허용 (보안상 나중엔 프론트 주소로 제한)
    # allow_origins=["http://localhost:3000","http://localhost:5173",],  # React(Vite) 개발 포트
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Hello from InsightFlow!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
