#!/usr/bin/env python3
"""
OKKY Jobs Backend 메인 실행 파일
"""

import uvicorn
import os
from src.okky_jobs.api.api_main import app

if __name__ == "__main__":
    # 환경 변수에서 포트와 호스트 설정
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8002))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    root_path = os.getenv("ROOT_PATH", "/okky")
    
    print(f"🚀 OKKY Jobs Backend 서버 시작")
    print(f"📍 주소: http://{host}:{port}")
    print(f"🔄 리로드: {reload}")
    print(f"🌐 Root Path: {root_path}")
    
    uvicorn.run(
        "src.okky_jobs.api.api_main:app",
        host=host,
        port=port,
        reload=reload,
        root_path=root_path
    )
