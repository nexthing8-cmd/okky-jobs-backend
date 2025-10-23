# 백엔드 구현 가이드 - OKKY Jobs 크롤링 시스템

## 📋 개요
프론트엔드에서 요구하는 실시간 크롤링 로그 및 히스토리 기능을 위한 백엔드 API 구현 가이드입니다.

## 🔧 구현 필요 API 엔드포인트

### 1. 기존 API (이미 구현됨)
```
GET /okky/search          # 채용공고 검색
GET /okky/search/{id}     # 채용공고 상세 조회
GET /okky/crawl/status    # 크롤링 상태 조회
POST /okky/crawl          # 크롤링 실행
```

### 2. 새로 구현해야 하는 API

#### 📝 크롤링 로그 관련

**기본 로그 조회**
```http
GET /okky/crawl/logs
```

**Response:**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "type": "info",
        "message": "크롤링 시스템이 준비되었습니다.",
        "timestamp": "2025-10-23T11:20:00Z"
      },
      {
        "type": "success", 
        "message": "마지막 크롤링이 성공적으로 완료되었습니다.",
        "timestamp": "2025-10-23T10:20:00Z"
      }
    ]
  }
}
```

**실시간 로그 조회**
```http
GET /okky/crawl/logs/realtime
```

**Response:**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "type": "info",
        "message": "크롤링 시작: OKKY 채용공고 수집",
        "timestamp": "2025-10-23T11:20:00Z"
      },
      {
        "type": "progress",
        "message": "페이지 1/10 처리 중... (15개 공고 수집)",
        "timestamp": "2025-10-23T11:20:15Z",
        "progress": 10
      },
      {
        "type": "success",
        "message": "총 150개 공고 수집 완료",
        "timestamp": "2025-10-23T11:25:00Z"
      }
    ],
    "isRunning": true,
    "currentProgress": 10
  }
}
```

#### 📊 크롤링 히스토리 관련

**크롤링 히스토리 조회**
```http
GET /okky/crawl/history
```

**Response:**
```json
{
  "success": true,
  "data": {
    "history": [
      {
        "id": 1,
        "status": "완료",
        "startedAt": "2025-10-23T10:15:17Z",
        "endedAt": "2025-10-23T10:25:17Z",
        "duration": 600000,
        "processed": 150
      },
      {
        "id": 2,
        "status": "완료",
        "startedAt": "2025-10-23T09:15:17Z",
        "endedAt": "2025-10-23T09:25:17Z",
        "duration": 600000,
        "processed": 120
      }
    ]
  }
}
```

#### 🛑 크롤링 중지 관련

**크롤링 중지**
```http
POST /okky/crawl/stop
```

**Response:**
```json
{
  "success": true,
  "message": "크롤링이 중지되었습니다."
}
```

## 🗄️ 데이터베이스 스키마

### 크롤링 로그 테이블
```sql
CREATE TABLE crawling_logs (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL,  -- info, success, error, warning, progress
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    progress INTEGER DEFAULT NULL,  -- 진행률 (0-100)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_crawling_logs_timestamp ON crawling_logs(timestamp);
CREATE INDEX idx_crawling_logs_type ON crawling_logs(type);
```

### 크롤링 히스토리 테이블
```sql
CREATE TABLE crawling_history (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) NOT NULL,  -- 완료, 실패, 진행중
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration INTEGER,  -- 밀리초
    processed INTEGER DEFAULT 0,  -- 처리된 항목 수
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_crawling_history_started_at ON crawling_history(started_at);
CREATE INDEX idx_crawling_history_status ON crawling_history(status);
```

## 🔄 실시간 로그 구현 방법

### 방법 1: 폴링 (Polling) - 권장

**Python FastAPI 예시:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/crawl/logs")
async def get_crawling_logs(db: Session = Depends(get_db)):
    """기본 크롤링 로그 조회"""
    logs = db.query(CrawlingLog).order_by(CrawlingLog.timestamp.desc()).limit(100).all()
    
    return {
        "success": True,
        "data": {
            "logs": [
                {
                    "type": log.type,
                    "message": log.message,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in logs
            ]
        }
    }

@router.get("/crawl/logs/realtime")
async def get_realtime_logs(db: Session = Depends(get_db)):
    """실시간 크롤링 로그 조회"""
    # 현재 크롤링 상태 확인
    is_running = check_crawling_status()
    
    if is_running:
        # 최근 50개 로그 가져오기
        logs = db.query(CrawlingLog).order_by(CrawlingLog.timestamp.desc()).limit(50).all()
        progress = get_current_progress()
        
        return {
            "success": True,
            "data": {
                "logs": [
                    {
                        "type": log.type,
                        "message": log.message,
                        "timestamp": log.timestamp.isoformat(),
                        "progress": log.progress
                    }
                    for log in logs
                ],
                "isRunning": True,
                "currentProgress": progress
            }
        }
    else:
        return {
            "success": True,
            "data": {
                "logs": [],
                "isRunning": False,
                "currentProgress": 0
            }
        }

@router.get("/crawl/history")
async def get_crawling_history(db: Session = Depends(get_db)):
    """크롤링 히스토리 조회"""
    history = db.query(CrawlingHistory).order_by(CrawlingHistory.started_at.desc()).limit(50).all()
    
    return {
        "success": True,
        "data": {
            "history": [
                {
                    "id": h.id,
                    "status": h.status,
                    "startedAt": h.started_at.isoformat(),
                    "endedAt": h.ended_at.isoformat() if h.ended_at else None,
                    "duration": h.duration,
                    "processed": h.processed
                }
                for h in history
            ]
        }
    }

@router.post("/crawl/stop")
async def stop_crawling():
    """크롤링 중지"""
    # 크롤링 프로세스 중지 로직
    stop_crawling_process()
    
    return {
        "success": True,
        "message": "크롤링이 중지되었습니다."
    }
```

### 방법 2: WebSocket (고급)

**WebSocket 실시간 통신:**
```python
from fastapi import WebSocket
import asyncio
import json

@app.websocket("/crawl/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # 크롤링 상태 모니터링
            if is_crawling_running():
                logs = get_new_logs()
                await websocket.send_json({
                    "type": "log_update",
                    "data": logs
                })
            
            await asyncio.sleep(2)  # 2초마다 체크
    except WebSocketDisconnect:
        print("WebSocket 연결이 끊어졌습니다.")
```

## 📝 크롤링 프로세스에서 로그 생성

### 로그 생성 클래스
```python
import logging
from datetime import datetime
from sqlalchemy.orm import Session

class CrawlingLogger:
    def __init__(self, db: Session):
        self.db = db
        self.logs = []
    
    def log_info(self, message: str):
        """정보 로그"""
        self.add_log("info", message)
    
    def log_progress(self, message: str, progress: int):
        """진행률 로그"""
        self.add_log("progress", message, progress)
    
    def log_success(self, message: str):
        """성공 로그"""
        self.add_log("success", message)
    
    def log_error(self, message: str):
        """에러 로그"""
        self.add_log("error", message)
    
    def log_warning(self, message: str):
        """경고 로그"""
        self.add_log("warning", message)
    
    def add_log(self, log_type: str, message: str, progress: int = None):
        """로그 추가"""
        log_entry = CrawlingLog(
            type=log_type,
            message=message,
            timestamp=datetime.now(),
            progress=progress
        )
        
        self.db.add(log_entry)
        self.db.commit()
        
        # 메모리에도 저장 (실시간 조회용)
        self.logs.append({
            "type": log_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "progress": progress
        })
```

### 크롤링 프로세스에서 사용
```python
def crawl_jobs(db: Session):
    """크롤링 실행 함수"""
    logger = CrawlingLogger(db)
    
    try:
        # 크롤링 히스토리 시작
        history = CrawlingHistory(
            status="진행중",
            started_at=datetime.now()
        )
        db.add(history)
        db.commit()
        
        logger.log_info("크롤링 시작: OKKY 채용공고 수집")
        
        total_processed = 0
        
        for page in range(1, 11):
            progress = page * 10
            logger.log_progress(f"페이지 {page}/10 처리 중...", progress)
            
            # 실제 크롤링 로직
            jobs = fetch_jobs_from_okky(page)
            total_processed += len(jobs)
            
            logger.log_info(f"{len(jobs)}개 공고 수집")
            
            # 데이터베이스에 저장
            save_jobs_to_db(jobs, db)
            
            # 잠시 대기 (서버 부하 방지)
            time.sleep(1)
        
        # 크롤링 완료
        history.status = "완료"
        history.ended_at = datetime.now()
        history.duration = int((history.ended_at - history.started_at).total_seconds() * 1000)
        history.processed = total_processed
        db.commit()
        
        logger.log_success(f"총 {total_processed}개 공고 수집 완료")
        
    except Exception as e:
        # 에러 처리
        logger.log_error(f"크롤링 중 오류 발생: {str(e)}")
        
        if 'history' in locals():
            history.status = "실패"
            history.ended_at = datetime.now()
            history.duration = int((history.ended_at - history.started_at).total_seconds() * 1000)
            db.commit()
        
        raise e
```

## 📊 API 응답 형식 통일

### 성공 응답
```json
{
  "success": true,
  "data": { ... },
  "message": "요청이 성공적으로 처리되었습니다."
}
```

### 에러 응답
```json
{
  "success": false,
  "error": {
    "code": "CRAWLING_ERROR",
    "message": "크롤링 실행 중 오류가 발생했습니다.",
    "details": "상세 에러 정보"
  }
}
```

## 🎯 구현 우선순위

### 1단계 (필수) - 기본 기능
- [ ] `GET /okky/crawl/logs` - 기본 로그 조회
- [ ] `GET /okky/crawl/history` - 히스토리 조회
- [ ] 크롤링 로그 테이블 생성
- [ ] 크롤링 히스토리 테이블 생성

### 2단계 (권장) - 실시간 기능
- [ ] `GET /okky/crawl/logs/realtime` - 실시간 로그
- [ ] `POST /okky/crawl/stop` - 크롤링 중지
- [ ] 크롤링 프로세스에 로그 생성 로직 추가
- [ ] 실시간 상태 모니터링

### 3단계 (고급) - 고급 기능
- [ ] WebSocket 실시간 통신
- [ ] 로그 레벨별 필터링
- [ ] 로그 검색 및 페이징
- [ ] 크롤링 성능 메트릭
- [ ] 로그 아카이빙 시스템

## 🔍 테스트 방법

### API 테스트
```bash
# 기본 로그 조회
curl -X GET "https://your-api-server.com/okky/crawl/logs"

# 실시간 로그 조회
curl -X GET "https://your-api-server.com/okky/crawl/logs/realtime"

# 크롤링 히스토리 조회
curl -X GET "https://your-api-server.com/okky/crawl/history"

# 크롤링 중지
curl -X POST "https://your-api-server.com/okky/crawl/stop"
```

### 프론트엔드 연동 확인
1. 크롤링 관리 페이지에서 "크롤링 시작" 버튼 클릭
2. 실시간 로그가 2초마다 업데이트되는지 확인
3. 크롤링 히스토리가 정상적으로 표시되는지 확인

## 📝 참고사항

- 프론트엔드는 2초마다 실시간 로그 API를 호출합니다
- 로그는 최근 50개까지만 반환하면 됩니다
- 크롤링이 진행 중일 때만 실시간 로그를 생성합니다
- 에러 발생 시 적절한 에러 로그를 생성해야 합니다
- 데이터베이스 연결 오류 시에도 로그 생성이 중단되지 않도록 해야 합니다

---

이 가이드를 따라 구현하면 프론트엔드에서 실시간으로 크롤링 진행 상황을 모니터링할 수 있습니다! 🚀
