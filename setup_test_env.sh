#!/bin/bash

# OKKY Jobs Backend 테스트 환경 설정 스크립트 (외부 데이터베이스 사용)

echo "🚀 OKKY Jobs Backend 테스트 환경 설정을 시작합니다..."

# 1. .env 파일 생성 (사용자 입력 받기)
echo "📝 .env 파일을 생성합니다..."
echo "외부 데이터베이스 정보를 입력해주세요:"

read -p "DB_HOST (예: your-db-host.com): " DB_HOST
read -p "DB_USER (예: your_username): " DB_USER
read -s -p "DB_PASSWORD: " DB_PASSWORD
echo ""
read -p "DB_NAME (예: your_database): " DB_NAME
read -p "DB_PORT (기본값: 3306): " DB_PORT
DB_PORT=${DB_PORT:-3306}

cat > .env << EOF
# 데이터베이스 설정 (외부 DB)
DB_HOST=${DB_HOST}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
DB_PORT=${DB_PORT}

# API 설정
ROOT_PATH=/okky

# Chrome 설정 (Docker 환경용)
GOOGLE_BIN=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/bin/chromedriver
EOF

echo "✅ .env 파일이 생성되었습니다."

# 2. Docker Compose로 서비스 시작
echo "🐳 Docker Compose로 서비스를 시작합니다..."
docker-compose up -d

# 3. 서비스 시작 대기
echo "⏳ 서비스 시작을 기다립니다..."
sleep 10

# 4. 데이터베이스 연결 테스트
echo "🔍 데이터베이스 연결을 테스트합니다..."
docker-compose exec okky-jobs-backend python -c "
from src.okky_jobs.db.db import get_connection
try:
    conn = get_connection()
    print('✅ 데이터베이스 연결 성공')
    conn.close()
except Exception as e:
    print(f'❌ 데이터베이스 연결 실패: {e}')
    exit(1)
"

# 5. API 서버 상태 확인
echo "🌐 API 서버 상태를 확인합니다..."
sleep 5
curl -s http://localhost:8002/ > /dev/null && echo "✅ API 서버가 정상적으로 실행 중입니다." || echo "❌ API 서버 연결 실패"

echo ""
echo "🎉 테스트 환경 설정이 완료되었습니다!"
echo ""
echo "다음 명령어로 테스트를 실행할 수 있습니다:"
echo "  pytest tests/"
echo "  curl http://localhost:8002/"
echo "  python -m src.okky_jobs.scripts.run_view"
echo ""
echo "서비스를 중지하려면:"
echo "  docker-compose down"
