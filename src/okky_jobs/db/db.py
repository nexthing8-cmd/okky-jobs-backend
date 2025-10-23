import sys
import os

import pymysql

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from typing import List, Optional
from dotenv import load_dotenv
from ..crawler.crawler_master import MasterJob
from .models import DetailJob

# ✅ .env 로드
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "crawling"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "crawling"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "charset": "utf8mb4",
    "autocommit": True
}

# ✅ DB 연결
def get_connection():
    return pymysql.connect(**DB_CONFIG)

# ✅ 마스터 공고 저장
def save_master_jobs(jobs: List[MasterJob]):
    sql = """
    INSERT INTO okky_jobs (title, company, link, deadline, category, position, location, career, salary)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        company = VALUES(company),
        deadline = VALUES(deadline),
        category = VALUES(category),
        position = VALUES(position),
        location = VALUES(location),
        career = VALUES(career),
        salary = VALUES(salary),
        updated_at = CURRENT_TIMESTAMP
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for j in jobs:
            cursor.execute(sql, (
                j.title, j.company, j.link, j.deadline, j.category,
                j.position, j.location, j.career, j.salary
            ))
        print(f"✅ 마스터 {len(jobs)}건 저장 완료")
    except Exception as e:
        print(f"❌ 마스터 저장 실패: {e}")
    finally:
        cursor.close()
        conn.close()

# ✅ 연락처 저장
def save_contact(conn, cursor, name: str, phone: str, email: str) -> Optional[int]:
    if not (name or phone or email):
        return None

    sql = """
    INSERT INTO okky_job_contacts (name, phone, email)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
        
        phone = VALUES(phone),
        email = VALUES(email),
        updated_at = CURRENT_TIMESTAMP
    """
    cursor.execute(sql, (name, phone, email))
    cursor.execute("SELECT id FROM okky_job_contacts WHERE name=%s AND phone=%s AND email=%s", (name, phone, email))
    result = cursor.fetchone()
    return result[0] if result else None

# ✅ 상세 공고 저장
def save_detail_jobs(detail_jobs: List[DetailJob]):
    sql = """
    INSERT INTO okky_job_details (
        link, registered_at, view_count, start_date, work_location,
        pay_date, skill, description, contact_id
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON DUPLICATE KEY UPDATE
        registered_at = VALUES(registered_at),
        view_count = VALUES(view_count),
        start_date = VALUES(start_date),
        work_location = VALUES(work_location),
        pay_date = VALUES(pay_date),
        skill = VALUES(skill),
        description = VALUES(description),
        contact_id = VALUES(contact_id),
        updated_at = CURRENT_TIMESTAMP
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for d in detail_jobs:
            contact_id = save_contact(conn, cursor, d.contact_name, d.contact_phone, d.contact_email)
            cursor.execute(sql, (
                d.link, d.registered_at, d.view_count, d.start_date,
                d.work_location, d.pay_date, d.skill, d.description,
                contact_id
            ))
        print(f"✅ 상세 {len(detail_jobs)}건 저장 완료")
    except Exception as e:
        print(f"❌ 상세 저장 실패: {e}")
    finally:
        cursor.close()
        conn.close()

# ✅ 전체 마스터 공고 조회
def get_all_jobs() -> List[MasterJob]:
    sql = """
    SELECT title, company, link, deadline, category, position, location, career, salary
    FROM okky_jobs
    ORDER BY created_at DESC
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [MasterJob(*row) for row in rows]
    finally:
        cursor.close()
        conn.close()

# ✅ 전체 상세 공고 조회
def get_all_details() -> List[DetailJob]:
    sql = """
    SELECT d.link, d.registered_at, d.view_count, d.start_date, d.work_location,
           d.pay_date, d.skill, d.description, c.name, c.phone, c.email
    FROM okky_job_details d
    LEFT JOIN okky_job_contacts c ON d.contact_id = c.id
    ORDER BY d.registered_at DESC
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [
            DetailJob(
                link=row[0], registered_at=row[1], view_count=row[2],
                start_date=row[3], work_location=row[4], pay_date=row[5],
                skill=row[6], description=row[7],
                contact_name=row[8], contact_phone=row[9], contact_email=row[10]
            )
            for row in rows
        ]
    finally:
        cursor.close()
        conn.close()

# ✅ 특정 상세 공고 조회
def get_detail_job_by_link(link: str) -> Optional[DetailJob]:
    sql = """
    SELECT d.link, d.registered_at, d.view_count, d.start_date, d.work_location,
           d.pay_date, d.skill, d.description, c.name, c.phone, c.email
    FROM okky_job_details d
    LEFT JOIN okky_job_contacts c ON d.contact_id = c.id
    WHERE d.link = %s
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (link,))
        row = cursor.fetchone()
        if row:
            return DetailJob(
                link=row[0], registered_at=row[1], view_count=row[2],
                start_date=row[3], work_location=row[4], pay_date=row[5],
                skill=row[6], description=row[7],
                contact_name=row[8], contact_phone=row[9], contact_email=row[10]
            )
        return None
    except Exception as e:
        print(f"❌ 상세 조회 실패: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def save_detail_job(detail_job: DetailJob):
    """단일 상세 공고 저장"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # ✅ 연락처 먼저 저장
        contact_id = None
        if detail_job.contact_name or detail_job.contact_phone or detail_job.contact_email:
            contact_id = save_contact(
                conn, cursor,
                detail_job.contact_name,
                detail_job.contact_phone,
                detail_job.contact_email
            )

        sql = """
        INSERT INTO okky_job_details (
            link, registered_at, view_count, start_date, work_location,
            pay_date, skill, description, contact_id
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            registered_at = VALUES(registered_at),
            view_count = VALUES(view_count),
            start_date = VALUES(start_date),
            work_location = VALUES(work_location),
            pay_date = VALUES(pay_date),
            skill = VALUES(skill),
            description = VALUES(description),
            contact_id = VALUES(contact_id),
            updated_at = CURRENT_TIMESTAMP
        """
        cursor.execute(sql, (
            detail_job.link,
            detail_job.registered_at,
            detail_job.view_count,
            detail_job.start_date,
            detail_job.work_location,
            detail_job.pay_date,
            detail_job.skill,
            detail_job.description,
            contact_id
        ))
        print(f"✅ 단건 상세 저장 완료: {detail_job.link}")
    except Exception as e:
        print(f"❌ 단건 상세 저장 실패: {e}")
    finally:
        cursor.close()
        conn.close()
