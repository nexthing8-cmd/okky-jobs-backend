import pandas as pd
from typing import List
from datetime import datetime
from ..crawler.crawler_master import MasterJob
from ..db.models import DetailJob


def timestamped_filename(base: str, ext: str = "xlsx") -> str:
    """기본 파일명에 타임스탬프(YYYY-MM-DD_hh-mm-ss) 포함"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # 파일에 적합한 포맷
    return f"{base}_{timestamp}.{ext}"


def save_jobs_to_excel(jobs: List[MasterJob], filename: str = None):
    """마스터 공고 데이터를 엑셀로 저장"""
    if not filename:
        filename = timestamped_filename("okky_jobs_export")
    data = [job._asdict() for job in jobs]
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"📁 마스터 공고 {len(jobs)}건 엑셀 저장 완료: {filename}")


def save_details_to_excel(details: List[DetailJob], filename: str = None):
    """상세 공고 데이터를 엑셀로 저장"""
    if not filename:
        filename = timestamped_filename("okky_details_export")
    data = [detail._asdict() for detail in details]
    df = pd.DataFrame(data)

    # ✅ datetime 포맷 지정
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.attrs["exported_at"] = now_str  # 엑셀 파일 자체에는 메타 데이터 못 들어감, 기록만 가능

    df.to_excel(filename, index=False)
    print(f"📁 상세 공고 {len(details)}건 엑셀 저장 완료: {filename}")


def export_to_excel(rows: List[dict], filename: str = None):
    """검색 결과 데이터를 엑셀로 저장"""
    if not rows:
        print("❌ 저장할 데이터가 없습니다.")
        return
    if not filename:
        filename = timestamped_filename("okky_search_export")
    df = pd.DataFrame(rows)

    # ✅ datetime 포맷 지정
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.attrs["exported_at"] = now_str

    df.to_excel(filename, index=False)
    print(f"📁 검색 결과 {len(rows)}건 엑셀 저장 완료: {filename}")
