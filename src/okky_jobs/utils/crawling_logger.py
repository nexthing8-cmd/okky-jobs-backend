"""
크롤링 로그 관리 클래스
"""

import pymysql
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


def get_connection():
    """데이터베이스 연결 생성"""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "crawling"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "crawling"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
        autocommit=True
    )


class CrawlingLogger:
    """크롤링 로그 관리 클래스"""
    
    def __init__(self):
        self.logs = []
        self.current_history_id = None
    
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
    
    def add_log(self, log_type: str, message: str, progress: Optional[int] = None):
        """로그 추가"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # 데이터베이스에 로그 저장
            sql = """
            INSERT INTO crawling_logs (type, message, timestamp, progress)
            VALUES (%s, %s, %s, %s)
            """
            now = datetime.now()
            cursor.execute(sql, (log_type, message, now, progress))
            conn.commit()
            
            # 메모리에도 저장 (실시간 조회용)
            self.logs.append({
                "type": log_type,
                "message": message,
                "timestamp": now.isoformat(),
                "progress": progress
            })
            
            # 최근 100개만 유지
            if len(self.logs) > 100:
                self.logs = self.logs[-100:]
                
        except Exception as e:
            print(f"❌ 로그 저장 실패: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def start_crawling_history(self) -> int:
        """크롤링 히스토리 시작"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
            INSERT INTO crawling_history (status, started_at, processed)
            VALUES (%s, %s, %s)
            """
            now = datetime.now()
            cursor.execute(sql, ("진행중", now, 0))
            conn.commit()
            
            # 생성된 ID 가져오기
            cursor.execute("SELECT LAST_INSERT_ID()")
            history_id = cursor.fetchone()[0]
            self.current_history_id = history_id
            
            return history_id
            
        except Exception as e:
            print(f"❌ 히스토리 시작 실패: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def update_crawling_history(self, status: str, processed: int = 0):
        """크롤링 히스토리 업데이트"""
        if not self.current_history_id:
            return
            
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            
            if status in ["완료", "실패"]:
                # 시작 시간 가져오기
                cursor.execute(
                    "SELECT started_at FROM crawling_history WHERE id = %s",
                    (self.current_history_id,)
                )
                result = cursor.fetchone()
                if result:
                    started_at = result[0]
                    duration = int((now - started_at).total_seconds() * 1000)
                    
                    sql = """
                    UPDATE crawling_history 
                    SET status = %s, ended_at = %s, duration = %s, processed = %s
                    WHERE id = %s
                    """
                    cursor.execute(sql, (status, now, duration, processed, self.current_history_id))
                else:
                    sql = """
                    UPDATE crawling_history 
                    SET status = %s, ended_at = %s, processed = %s
                    WHERE id = %s
                    """
                    cursor.execute(sql, (status, now, processed, self.current_history_id))
            else:
                sql = """
                UPDATE crawling_history 
                SET status = %s, processed = %s
                WHERE id = %s
                """
                cursor.execute(sql, (status, processed, self.current_history_id))
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ 히스토리 업데이트 실패: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """최근 로그 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
            SELECT type, message, timestamp, progress
            FROM crawling_logs
            ORDER BY timestamp DESC
            LIMIT %s
            """
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            
            return [
                {
                    "type": row[0],
                    "message": row[1],
                    "timestamp": row[2].isoformat(),
                    "progress": row[3]
                }
                for row in rows
            ]
            
        except Exception as e:
            print(f"❌ 로그 조회 실패: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def get_crawling_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """크롤링 히스토리 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
            SELECT id, status, started_at, ended_at, duration, processed
            FROM crawling_history
            ORDER BY started_at DESC
            LIMIT %s
            """
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row[0],
                    "status": row[1],
                    "startedAt": row[2].isoformat(),
                    "endedAt": row[3].isoformat() if row[3] else None,
                    "duration": row[4],
                    "processed": row[5]
                }
                for row in rows
            ]
            
        except Exception as e:
            print(f"❌ 히스토리 조회 실패: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def is_crawling_running(self) -> bool:
        """크롤링 실행 중인지 확인"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
            SELECT COUNT(*) FROM crawling_history 
            WHERE status = '진행중'
            """
            cursor.execute(sql)
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            print(f"❌ 크롤링 상태 확인 실패: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def get_current_progress(self) -> int:
        """현재 진행률 조회"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            sql = """
            SELECT progress FROM crawling_logs 
            WHERE type = 'progress' 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            cursor.execute(sql)
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
            
        except Exception as e:
            print(f"❌ 진행률 조회 실패: {e}")
            return 0
        finally:
            cursor.close()
            conn.close()
