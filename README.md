# OKKY Jobs Backend

OKKY 채용공고 크롤링 및 검색 API 백엔드 서비스입니다.

## 기능

- OKKY 채용공고 자동 크롤링
- 채용공고 검색 API
- 상세 정보 조회
- 엑셀 내보내기
- 스케줄링된 크롤링

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 데이터베이스 정보 입력
```

#### 테스트 환경 설정 (외부 데이터베이스 사용)

```bash
# 1. .env 파일 생성 (외부 데이터베이스 정보 입력)
cat > .env << EOF
# 데이터베이스 설정 (외부 DB 정보 입력)
DB_HOST=your_external_db_host
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_PORT=3306

# API 설정
ROOT_PATH=/okky

# Chrome 설정 (Docker 환경용)
GOOGLE_BIN=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/bin/chromedriver
EOF

# 2. Docker Compose로 애플리케이션 실행
docker-compose up -d

# 3. 데이터베이스 연결 확인
docker-compose exec okky-jobs-backend python -c "
from src.okky_jobs.db.db import get_connection
conn = get_connection()
print('✅ 데이터베이스 연결 성공')
conn.close()
"
```

### 3. API 서버 실행

```bash
# 개발 모드
uvicorn src.okky_jobs.api.api_main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn src.okky_jobs.api.api_main:app --host 0.0.0.0 --port 8000
```

### 4. 크롤링 실행

```bash
# 수동 크롤링
python -m src.okky_jobs.scripts.run_crawling

# 데이터 조회
python -m src.okky_jobs.scripts.run_view

# 스케줄러 실행
python -m src.okky_jobs.scheduler.scheduler
```

## API 엔드포인트

- `GET /` - API 상태 확인
- `GET /jobs` - 기본 채용공고 검색
- `GET /search` - 고급 채용공고 검색 (페이지네이션, 필터링)
- `GET /search/stats` - 통계 정보
- `GET /search/{job_id}` - 채용공고 상세 정보
- `GET /jobs/export` - 엑셀 내보내기
- `POST /crawl` - 수동 크롤링 실행
- `GET /crawl/status` - 크롤링 상태 확인

## 프로젝트 구조

```
src/
├── okky_jobs/
│   ├── api/           # FastAPI 엔드포인트
│   ├── crawler/       # 크롤링 로직
│   ├── db/           # 데이터베이스 모델 및 연결
│   ├── scheduler/    # 스케줄링
│   ├── scripts/      # 실행 스크립트
│   └── utils/        # 유틸리티 함수
tests/                 # 테스트 파일
```

## 서버 배포

### 프로덕션 환경 설정

```bash
# 1. 환경 변수 설정 (서버용)
cat > .env << EOF
# 데이터베이스 설정
DB_HOST=your_production_db_host
DB_USER=your_production_user
DB_PASSWORD=your_production_password
DB_NAME=your_production_database
DB_PORT=3306

# API 설정 (서버 배포용)
ROOT_PATH=/okky

# Chrome 설정
GOOGLE_BIN=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/bin/chromedriver
EOF

# 2. amd64 플랫폼으로 빌드 및 실행
docker-compose up -d --build

# 3. 서비스 상태 확인
docker-compose ps
curl http://localhost:8002/
```

### 리버스 프록시 설정 (Nginx 예시)

```nginx
# ✅ OKKY API 백엔드 (8002번 → /okky 로 reverse proxy)
location = /okky { return 301 /okky/; }  # 슬래시 정규화

# /okky/ 경로 처리 (OKKY API)
location /okky/ {
    proxy_pass http://127.0.0.1:8002/;  # ← 슬래시 유지 중요
    proxy_http_version 1.1;
    proxy_set_header Host              $host:$server_port;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header Connection        "";
    proxy_set_header Upgrade           $http_upgrade;

    # OpenAPI JSON 경로 수정을 위한 헤더 추가
    proxy_set_header X-Forwarded-Prefix /okky;
}
```

## 개발

### 테스트 실행

```bash
# 기본 테스트 실행
pytest tests/

# Docker 환경에서 테스트 실행
docker-compose exec okky-jobs-backend pytest tests/

# 특정 테스트 실행
pytest tests/okky_jobs/test_view_detail.py -v
```

#### 테스트 환경 확인

```bash
# 1. 데이터베이스 연결 테스트
python -c "
from src.okky_jobs.db.db import get_connection
conn = get_connection()
print('✅ 데이터베이스 연결 성공')
conn.close()
"

# 2. API 서버 테스트
curl http://localhost:8000/

# 3. 크롤링 테스트 (선택사항)
python -m src.okky_jobs.scripts.run_crawling
```

### 코드 포맷팅

```bash
black src/
isort src/
```
