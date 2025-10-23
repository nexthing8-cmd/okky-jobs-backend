from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from threading import Thread
import pymysql
import os
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

from ..db.db import get_connection
from ..utils.excel_utils import export_to_excel
from ..utils.crawling_logger import CrawlingLogger
from ..scheduler.scheduler import job

# 열거형 정의
class Category(str, Enum):
    개발 = "개발"
    디자인 = "디자인"
    기획 = "기획"
    마케팅 = "마케팅"
    영업 = "영업"

class Location(str, Enum):
    서울 = "서울"
    경기 = "경기"
    인천 = "인천"
    부산 = "부산"
    대구 = "대구"
    광주 = "광주"
    대전 = "대전"
    울산 = "울산"
    세종 = "세종"
    기타 = "기타"

class Experience(str, Enum):
    신입 = "신입"
    경력1_3년 = "1-3년"
    경력3_5년 = "3-5년"
    경력5_10년 = "5-10년"
    경력10년이상 = "10년 이상"

class Deadline(str, Enum):
    today = "today"
    three_days = "3days"
    one_week = "1week"
    one_month = "1month"

class SortBy(str, Enum):
    createdAt = "createdAt"
    company = "company"
    deadline = "deadline"
    views = "views"

# 데이터 모델 정의
class JobSearchResult(BaseModel):
    id: str
    company: str
    title: str
    category: str
    location: str
    experience: str
    deadline: Optional[str]
    views: int
    createdAt: str
    updatedAt: str
    originalUrl: str

class JobDetail(BaseModel):
    id: str
    company: str
    title: str
    category: str
    location: str
    experience: str
    deadline: Optional[str]
    views: int
    createdAt: str
    updatedAt: str
    originalUrl: str
    description: str
    requirements: str
    techStack: List[str]
    contact: Dict[str, str]

class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    totalPages: int
    hasNext: bool
    hasPrev: bool

class SearchResponse(BaseModel):
    success: bool
    data: List[JobSearchResult]
    pagination: PaginationInfo
    filters: Dict[str, Any]

class JobDetailResponse(BaseModel):
    success: bool
    data: JobDetail

class StatsResponse(BaseModel):
    success: bool
    data: Dict[str, Any]

# 검색 쿼리 빌더
def build_search_query(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    experience: Optional[str] = None,
    deadline: Optional[str] = None,
    sort: str = "createdAt",
    page: int = 1,
    limit: int = 20
) -> tuple:
    """검색 조건에 따른 SQL 쿼리를 빌드합니다."""
    
    # 기본 쿼리 (실제 테이블 구조에 맞게 수정)
    base_query = """
    SELECT 
        j.id,
        j.company,
        j.title,
        j.category,
        j.location,
        j.career as experience,
        j.deadline,
        COALESCE(d.view_count, 0) as views,
        j.created_at,
        j.updated_at,
        j.link as original_url
    FROM okky_jobs j
    LEFT JOIN okky_job_details d ON j.link = d.link
    WHERE 1=1
    """
    
    count_query = "SELECT COUNT(*) as total FROM okky_jobs j LEFT JOIN okky_job_details d ON j.link = d.link WHERE 1=1"
    
    params = []
    
    # 키워드 검색 (제목, 회사명에서 검색)
    if keyword:
        keyword_condition = """
        AND (j.title LIKE %s OR j.company LIKE %s)
        """
        base_query += keyword_condition
        count_query += keyword_condition
        keyword_param = f"%{keyword}%"
        params.extend([keyword_param, keyword_param])
    
    # 카테고리 필터
    if category:
        base_query += " AND j.category = %s"
        count_query += " AND j.category = %s"
        params.append(category)
    
    # 지역 필터
    if location:
        base_query += " AND j.location = %s"
        count_query += " AND j.location = %s"
        params.append(location)
    
    # 경력 필터
    if experience:
        base_query += " AND j.career = %s"
        count_query += " AND j.career = %s"
        params.append(experience)
    
    # 마감일 필터 (deadline이 VARCHAR이므로 문자열 비교)
    if deadline:
        today = datetime.now().date()
        if deadline == "today":
            deadline_date = today.strftime("%Y-%m-%d")
        elif deadline == "3days":
            deadline_date = (today + timedelta(days=3)).strftime("%Y-%m-%d")
        elif deadline == "1week":
            deadline_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif deadline == "1month":
            deadline_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            deadline_date = today.strftime("%Y-%m-%d")
        
        # deadline이 VARCHAR이므로 문자열 비교 사용
        base_query += " AND j.deadline <= %s"
        count_query += " AND j.deadline <= %s"
        params.append(deadline_date)
    
    # 정렬
    sort_mapping = {
        "createdAt": "j.created_at DESC",
        "company": "j.company ASC",
        "deadline": "j.deadline ASC",
        "views": "COALESCE(d.view_count, 0) DESC"
    }
    
    order_by = sort_mapping.get(sort, "j.created_at DESC")
    base_query += f" ORDER BY {order_by}"
    
    # 페이지네이션
    offset = (page - 1) * limit
    base_query += f" LIMIT {limit} OFFSET {offset}"
    
    return base_query, count_query, params

# 환경에 따라 root_path 동적 설정
# 서버 배포 시: /okky (리버스 프록시용), 로컬 개발 시: /
root_path = os.getenv("ROOT_PATH", "/okky")

app = FastAPI(
    title="OKKY 채용공고 검색 API", 
    version="1.0.0",
    root_path=root_path  # 환경 변수로 동적 설정
)

# 리버스 프록시를 위한 미들웨어 추가
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # X-Forwarded-Prefix 헤더가 있으면 root_path로 사용
    forwarded_prefix = request.headers.get("X-Forwarded-Prefix")
    if forwarded_prefix:
        request.scope["root_path"] = forwarded_prefix
    response = await call_next(request)
    return response

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def search_jobs(keyword: Optional[str] = None) -> List[dict]:
    """DB에서 키워드 기반 검색 결과 반환"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        sql = """
            SELECT 
                j.title, j.company, j.link, j.deadline, j.category, j.position, j.location,
                j.career, j.salary,
                d.registered_at, d.view_count, d.start_date, d.work_location,
                d.pay_date, d.skill, d.description,
                c.name AS contact_name, c.phone AS contact_phone, c.email AS contact_email
            FROM okky_jobs j
            LEFT JOIN okky_job_details d ON j.link = d.link  -- ✅ 링크 기준으로 조인
            LEFT JOIN okky_job_contacts c ON d.contact_id = c.id
        """
        params = ()
        if keyword:
            sql += " WHERE j.title LIKE %s OR j.company LIKE %s OR d.description LIKE %s"
            params = (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")
        sql += " ORDER BY j.created_at DESC"

        cursor.execute(sql, params)
        return cursor.fetchall()

    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


#@app.on_event("startup")
#def startup_event():
#    Thread(target=job, daemon=True).start()


@app.get("/")
async def root():
    return {"message": "OKKY 채용공고 검색 API입니다. /jobs 또는 /jobs/export 엔드포인트를 사용하세요."}


@app.get("/jobs")
async def get_jobs(keyword: Optional[str] = Query(None)):
    rows = search_jobs(keyword)
    if not rows:
        return JSONResponse(content={"message": "검색 결과가 없습니다."}, status_code=404)
    return JSONResponse(content=rows)

# 새로운 채용공고 검색 API 엔드포인트들
@app.get("/search", response_model=SearchResponse)
async def search_jobs_new(
    keyword: Optional[str] = Query(None, description="검색 키워드"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    location: Optional[str] = Query(None, description="지역 필터"),
    experience: Optional[str] = Query(None, description="경력 필터"),
    deadline: Optional[str] = Query(None, description="마감일 필터 (today, 3days, 1week, 1month)"),
    sort: str = Query("createdAt", description="정렬 기준 (createdAt, company, deadline, views)")
):
    """채용공고 검색 API"""
    try:
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 검색 쿼리 빌드
        search_query, count_query, params = build_search_query(
            keyword=keyword,
            category=category,
            location=location,
            experience=experience,
            deadline=deadline,
            sort=sort,
            page=page,
            limit=limit
        )
        
        # 총 개수 조회
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # 검색 결과 조회
        cursor.execute(search_query, params)
        results = cursor.fetchall()
        
        # 결과 변환
        jobs = []
        for row in results:
            jobs.append(JobSearchResult(
                id=str(row['id']),
                company=row['company'],
                title=row['title'],
                category=row['category'],
                location=row['location'],
                experience=row['experience'],  # career as experience로 매핑됨
                deadline=row['deadline'] if row['deadline'] else None,
                views=row['views'] or 0,
                createdAt=row['created_at'].isoformat() if row['created_at'] else None,
                updatedAt=row['updated_at'].isoformat() if row['updated_at'] else None,
                originalUrl=row['original_url']
            ))
        
        # 페이지네이션 정보 계산
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination = PaginationInfo(
            page=page,
            limit=limit,
            total=total,
            totalPages=total_pages,
            hasNext=has_next,
            hasPrev=has_prev
        )
        
        # 필터 정보
        filters = {
            "keyword": keyword,
            "category": category,
            "location": location,
            "experience": experience,
            "deadline": deadline,
            "sort": sort
        }
        
        cursor.close()
        conn.close()
        
        return SearchResponse(
            success=True,
            data=jobs,
            pagination=pagination,
            filters=filters
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

@app.get("/search/stats", response_model=StatsResponse)
async def get_stats():
    """통계 정보 조회"""
    try:
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 전체 채용공고 수
        cursor.execute("SELECT COUNT(*) as total FROM okky_jobs")
        total_jobs = cursor.fetchone()['total']
        
        # 오늘 등록된 채용공고 수
        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*) as today FROM okky_jobs WHERE DATE(created_at) = %s", (today,))
        today_jobs = cursor.fetchone()['today']
        
        # 마지막 업데이트 시간
        cursor.execute("SELECT MAX(updated_at) as last_update FROM okky_jobs")
        last_update = cursor.fetchone()['last_update']
        
        # 카테고리별 통계
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM okky_jobs
            GROUP BY category
            ORDER BY count DESC
        """)
        category_stats = {row['category']: row['count'] for row in cursor.fetchall()}
        
        stats = {
            "totalJobs": total_jobs,
            "todayJobs": today_jobs,
            "lastUpdate": last_update.isoformat() if last_update else None,
            "categoryStats": category_stats
        }
        
        cursor.close()
        conn.close()
        
        return StatsResponse(success=True, data=stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/search/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(job_id: str):
    """채용공고 상세 정보 조회"""
    try:
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 기본 정보 조회
        cursor.execute("""
            SELECT 
                j.id,
                j.company,
                j.title,
                j.category,
                j.location,
                j.career as experience,
                j.deadline,
                COALESCE(d.view_count, 0) as views,
                j.created_at,
                j.updated_at,
                j.link as original_url
            FROM okky_jobs j
            LEFT JOIN okky_job_details d ON j.link = d.link
            WHERE j.id = %s
        """, (job_id,))
        
        job = cursor.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="채용공고를 찾을 수 없습니다.")
        
        # 기술 스택 조회 (상세 테이블에서)
        cursor.execute("""
            SELECT skill
            FROM okky_job_details
            WHERE link = (SELECT link FROM okky_jobs WHERE id = %s)
        """, (job_id,))
        
        tech_stack = [row['skill'] for row in cursor.fetchall() if row['skill']]
        
        # 연락처 정보 조회
        cursor.execute("""
            SELECT c.name, c.phone, c.email
            FROM okky_job_contacts c
            JOIN okky_job_details d ON c.id = d.contact_id
            WHERE d.link = (SELECT link FROM okky_jobs WHERE id = %s)
        """, (job_id,))
        
        contact_row = cursor.fetchone()
        contact = {
            "name": contact_row['name'] if contact_row else None,
            "phone": contact_row['phone'] if contact_row else None,
            "email": contact_row['email'] if contact_row else None
        } if contact_row else {}
        
        # 조회수 증가 (okky_job_details 테이블에서)
        cursor.execute("""
            UPDATE okky_job_details 
            SET view_count = view_count + 1 
            WHERE link = (SELECT link FROM okky_jobs WHERE id = %s)
        """, (job_id,))
        conn.commit()
        
        job_detail = JobDetail(
            id=str(job['id']),
            company=job['company'],
            title=job['title'],
            category=job['category'],
            location=job['location'],
            experience=job['experience'],
            deadline=job['deadline'] if job['deadline'] else None,
            views=(job['views'] or 0) + 1,
            createdAt=job['created_at'].isoformat() if job['created_at'] else None,
            updatedAt=job['updated_at'].isoformat() if job['updated_at'] else None,
            originalUrl=job['original_url'],
            description="",  # 기본값
            requirements="",  # 기본값
            techStack=tech_stack,
            contact=contact
        )
        
        cursor.close()
        conn.close()
        
        return JobDetailResponse(success=True, data=job_detail)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상세 정보 조회 중 오류가 발생했습니다: {str(e)}")


@app.get("/jobs/export")
async def export_jobs(keyword: Optional[str] = Query(None)):
    rows = search_jobs(keyword)
    if not rows:
        return JSONResponse(content={"message": "검색 결과가 없습니다."}, status_code=404)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"okky_jobs_export_{timestamp}.xlsx".replace(":", "-")
    export_to_excel(rows, filename)

    return FileResponse(
        path=filename,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.post("/crawl")
async def manual_crawl():
    """
    수동 크롤링 실행 엔드포인트
    마스터 크롤링 → 상세 크롤링 → DB 저장을 순차적으로 실행
    """
    try:
        # 백그라운드에서 크롤링 실행
        def run_crawling():
            try:
                from ..crawler.crawler_master import crawl_all_master_jobs
                from ..crawler.crawler_detail import crawl_detail_jobs
                from ..db.db import save_master_jobs, save_detail_jobs
                
                print("🕷️ [수동 크롤링] 마스터 크롤링 시작...")
                master_jobs = crawl_all_master_jobs()
                
                if master_jobs:
                    print(f"✅ [수동 크롤링] {len(master_jobs)}건의 마스터 공고 수집")
                    save_master_jobs(master_jobs)
                    print("✅ [수동 크롤링] 마스터 공고 DB 저장 완료")
                    
                    print("🕷️ [수동 크롤링] 상세 크롤링 시작...")
                    detail_jobs = crawl_detail_jobs(master_jobs)
                    
                    if detail_jobs:
                        print(f"✅ [수동 크롤링] {len(detail_jobs)}건의 상세 공고 수집")
                        save_detail_jobs(detail_jobs)
                        print("✅ [수동 크롤링] 상세 공고 DB 저장 완료")
                    else:
                        print("⚠️ [수동 크롤링] 상세 공고가 없습니다")
                else:
                    print("⚠️ [수동 크롤링] 마스터 공고가 없습니다")
                    
                print("🎉 [수동 크롤링] 모든 크롤링 작업 완료!")
                
            except Exception as e:
                print(f"❌ [수동 크롤링] 오류 발생: {str(e)}")
        
        # 별도 스레드에서 크롤링 실행
        thread = Thread(target=run_crawling)
        thread.daemon = True
        thread.start()
        
        return JSONResponse({
            "message": "크롤링이 백그라운드에서 시작되었습니다",
            "status": "started",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": f"크롤링 시작 실패: {str(e)}",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/crawl/status")
async def crawl_status():
    """
    크롤링 상태 확인 엔드포인트
    """
    try:
        # 최근 크롤링된 데이터 개수 확인
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 마스터 공고 개수
        cursor.execute("SELECT COUNT(*) as count FROM okky_jobs")
        master_count = cursor.fetchone()['count']
        
        # 상세 공고 개수
        cursor.execute("SELECT COUNT(*) as count FROM okky_job_details")
        detail_count = cursor.fetchone()['count']
        
        # 최근 업데이트 시간
        cursor.execute("SELECT MAX(created_at) as last_update FROM okky_jobs")
        last_update = cursor.fetchone()['last_update']
        
        conn.close()
        
        return JSONResponse({
            "master_jobs_count": master_count,
            "detail_jobs_count": detail_count,
            "last_update": last_update.isoformat() if last_update else None,
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "message": f"상태 확인 실패: {str(e)}",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        )

# ==================== 크롤링 로그 및 히스토리 API ====================

@app.get("/crawl/logs")
async def get_crawling_logs():
    """기본 크롤링 로그 조회"""
    try:
        logger = CrawlingLogger()
        logs = logger.get_recent_logs(100)
        
        return {
            "success": True,
            "data": {
                "logs": logs
            }
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "LOGS_FETCH_ERROR",
                    "message": "로그 조회 중 오류가 발생했습니다.",
                    "details": str(e)
                }
            }
        )

@app.get("/crawl/logs/realtime")
async def get_realtime_logs():
    """실시간 크롤링 로그 조회"""
    try:
        logger = CrawlingLogger()
        is_running = logger.is_crawling_running()
        
        if is_running:
            logs = logger.get_recent_logs(50)
            progress = logger.get_current_progress()
            
            return {
                "success": True,
                "data": {
                    "logs": logs,
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
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "REALTIME_LOGS_ERROR",
                    "message": "실시간 로그 조회 중 오류가 발생했습니다.",
                    "details": str(e)
                }
            }
        )

@app.get("/crawl/history")
async def get_crawling_history():
    """크롤링 히스토리 조회"""
    try:
        logger = CrawlingLogger()
        history = logger.get_crawling_history(50)
        
        return {
            "success": True,
            "data": {
                "history": history
            }
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "HISTORY_FETCH_ERROR",
                    "message": "히스토리 조회 중 오류가 발생했습니다.",
                    "details": str(e)
                }
            }
        )

@app.post("/crawl/stop")
async def stop_crawling():
    """크롤링 중지"""
    try:
        logger = CrawlingLogger()
        
        # 진행 중인 크롤링 히스토리를 실패로 업데이트
        if logger.is_crawling_running():
            logger.update_crawling_history("실패", 0)
            logger.log_warning("크롤링이 사용자에 의해 중지되었습니다.")
        
        return {
            "success": True,
            "message": "크롤링이 중지되었습니다."
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "CRAWLING_STOP_ERROR",
                    "message": "크롤링 중지 중 오류가 발생했습니다.",
                    "details": str(e)
                }
            }
        )
