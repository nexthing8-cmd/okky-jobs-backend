#!/bin/bash

# OKKY Jobs Backend 서버 배포 스크립트

echo "🚀 OKKY Jobs Backend 서버 배포를 시작합니다..."

# 1. 환경 변수 확인
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다. 먼저 환경 변수를 설정해주세요."
    echo "예시:"
    echo "cat > .env << EOF"
    echo "DB_HOST=your_production_db_host"
    echo "DB_USER=your_production_user"
    echo "DB_PASSWORD=your_production_password"
    echo "DB_NAME=your_production_database"
    echo "DB_PORT=3306"
    echo "ROOT_PATH=/okky"
    echo "GOOGLE_BIN=/usr/bin/google-chrome"
    echo "CHROMEDRIVER_PATH=/usr/bin/chromedriver"
    echo "EOF"
    exit 1
fi

echo "✅ .env 파일 확인 완료"

# 2. 기존 컨테이너 정리
echo "🧹 기존 컨테이너를 정리합니다..."
docker-compose down

# 3. amd64 플랫폼으로 빌드 및 실행
echo "🔨 amd64 플랫폼으로 이미지를 빌드합니다..."
docker-compose build --platform linux/amd64

echo "🚀 서비스를 시작합니다..."
docker-compose up -d

# 4. 서비스 시작 대기
echo "⏳ 서비스 시작을 기다립니다..."
sleep 15

# 5. 서비스 상태 확인
echo "🔍 서비스 상태를 확인합니다..."
docker-compose ps

# 6. API 서버 연결 테스트
echo "🌐 API 서버 연결을 테스트합니다..."
if curl -s http://localhost:8002/ > /dev/null; then
    echo "✅ API 서버가 정상적으로 실행 중입니다."
    echo "📍 서버 주소: http://localhost:8002/"
    echo "📍 리버스 프록시 경로: https://your-domain.com/okky/"
else
    echo "❌ API 서버 연결 실패"
    echo "로그를 확인해주세요:"
    echo "docker-compose logs okky-jobs-backend"
    exit 1
fi

# 7. 데이터베이스 연결 테스트
echo "🗄️ 데이터베이스 연결을 테스트합니다..."
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

echo ""
echo "🎉 서버 배포가 완료되었습니다!"
echo ""
echo "📋 서비스 정보:"
echo "  - 내부 API 서버: http://localhost:8002/"
echo "  - 외부 접근 경로: https://your-domain.com/okky/"
echo "  - API 문서: https://your-domain.com/okky/docs"
echo "  - 상태 확인: curl http://localhost:8002/"
echo ""
echo "🔧 관리 명령어:"
echo "  - 로그 확인: docker-compose logs -f"
echo "  - 서비스 중지: docker-compose down"
echo "  - 서비스 재시작: docker-compose restart"
