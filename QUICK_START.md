# OKKY Jobs Backend - 빠른 시작 가이드

## 🚀 빠른 실행

### 1. 환경 설정
```bash
cd /Users/newbie/develop/cursor/okky-jobs-backend

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp env.example .env
# .env 파일을 편집하여 데이터베이스 정보 입력
```

### 2. API 서버 실행
```bash
# 개발 모드 (자동 리로드)
python main.py

# 또는 직접 uvicorn 실행
uvicorn src.okky_jobs.api.api_main:app --reload --host 0.0.0.0 --port 8002
```

### 3. API 테스트
```bash
# API 상태 확인
curl http://localhost:8002/

# 채용공고 검색
curl "http://localhost:8002/search?keyword=python&page=1&limit=10"

# 통계 정보
curl http://localhost:8002/search/stats
```

## 🐳 Docker 실행

### 1. Docker Compose로 실행
```bash
# 환경 변수 설정
cp env.example .env
# .env 파일 편집

# 서비스 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f okky-jobs-backend
```

### 2. 개별 Docker 실행
```bash
# 이미지 빌드
docker build -t okky-jobs-backend .

# 컨테이너 실행
docker run -p 8002:8002 --env-file .env okky-jobs-backend
```

## 📋 주요 명령어

### 크롤링 실행
```bash
# 수동 크롤링
python -m src.okky_jobs.scripts.run_crawling

# 데이터 조회 및 엑셀 내보내기
python -m src.okky_jobs.scripts.run_view

# 스케줄러 실행 (매일 12:00에 자동 크롤링)
python -m src.okky_jobs.scheduler.scheduler
```

### 테스트 실행
```bash
# 모든 테스트
pytest

# 특정 테스트
pytest tests/okky_jobs/test_detail_crawling.py
```

## 🔧 문제 해결

### Import 오류
```bash
# PYTHONPATH 설정
export PYTHONPATH=/Users/newbie/develop/cursor/okky-jobs-backend:$PYTHONPATH
```

### Chrome 드라이버 오류
```bash
# Chrome 설치 확인
google-chrome --version

# ChromeDriver 설치
pip install webdriver-manager
```

### 데이터베이스 연결 오류
- `.env` 파일의 데이터베이스 정보 확인
- 데이터베이스 서버 접근 가능 여부 확인
- 방화벽 설정 확인

## 📁 프로젝트 구조

```
okky-jobs-backend/
├── src/okky_jobs/          # 메인 소스 코드
│   ├── api/               # FastAPI 엔드포인트
│   ├── crawler/           # 크롤링 로직
│   ├── db/               # 데이터베이스 모델
│   ├── scheduler/        # 스케줄링
│   ├── scripts/          # 실행 스크립트
│   └── utils/            # 유틸리티
├── tests/                # 테스트 파일
├── sql/                  # SQL 스키마
├── main.py              # 메인 실행 파일
├── requirements.txt     # Python 의존성
├── Dockerfile          # Docker 설정
└── docker-compose.yml  # Docker Compose 설정
```
