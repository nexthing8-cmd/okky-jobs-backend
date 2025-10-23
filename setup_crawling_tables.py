#!/usr/bin/env python3
"""
크롤링 로그 및 히스토리 테이블 생성 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.okky_jobs.db.db import get_connection

def create_crawling_tables():
    """크롤링 관련 테이블 생성"""
    
    # 크롤링 로그 테이블 생성
    create_logs_table = """
    CREATE TABLE IF NOT EXISTS crawling_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        type VARCHAR(20) NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        progress INT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # 크롤링 히스토리 테이블 생성
    create_history_table = """
    CREATE TABLE IF NOT EXISTS crawling_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        status VARCHAR(20) NOT NULL,
        started_at TIMESTAMP NOT NULL,
        ended_at TIMESTAMP NULL,
        duration INT NULL,
        processed INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # 인덱스 생성
    create_logs_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_crawling_logs_timestamp ON crawling_logs(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_crawling_logs_type ON crawling_logs(type)"
    ]
    
    create_history_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_crawling_history_started_at ON crawling_history(started_at)",
        "CREATE INDEX IF NOT EXISTS idx_crawling_history_status ON crawling_history(status)"
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print("🗄️ 크롤링 로그 테이블 생성 중...")
        cursor.execute(create_logs_table)
        
        print("🗄️ 크롤링 히스토리 테이블 생성 중...")
        cursor.execute(create_history_table)
        
        print("📊 인덱스 생성 중...")
        for index_sql in create_logs_indexes + create_history_indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        print("✅ 크롤링 관련 테이블이 성공적으로 생성되었습니다!")
        
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_crawling_tables()
