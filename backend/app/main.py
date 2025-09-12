from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .routers import project, data, chat

# --- 기본 설정 ---

# 프로젝트 기본 경로 설정 (backend/ -> nlp-data-analyst/)
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

# FastAPI 앱 초기화
app = FastAPI(title="Talk2Data MVP")

# --- 라우터 포함 ---

# 각 기능별 API 라우터 추가
app.include_router(project.router)
app.include_router(data.router)
app.include_router(chat.router)

# --- 미들웨어 설정 ---

# CORS(Cross-Origin Resource Sharing) 미들웨어 추가
# 모든 오리진, 모든 메소드, 모든 헤더를 허용 (개발용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 정적 파일 및 기본 경로 ---

@app.get("/api/health")
def health():
    """API 서버의 상태를 확인하는 헬스 체크 엔드포인트"""
    return {"ok": True}

# 프론트엔드 파일 서빙
# 모든 경로를 frontend 디렉토리의 정적 파일로 마운트하고, 경로가 파일이 아닐 경우 index.html을 반환합니다.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
