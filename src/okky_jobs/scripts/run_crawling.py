import sys
import os

# ✅ 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ..crawler.crawler_master import crawl_all_master_jobs
from ..crawler.crawler_detail import crawl_detail_jobs
from ..db.db import save_master_jobs, save_detail_jobs


def run():
    print("\n=== [수동 실행] OKKY 전체 크롤링 시작 ===")
    try:
        # ✅ 1) 마스터 크롤링 및 저장
        master_jobs = crawl_all_master_jobs()
        if master_jobs:
            save_master_jobs(master_jobs)

        # ✅ 2) 상세 크롤링 및 저장
        detail_jobs = crawl_detail_jobs(master_jobs)
        if detail_jobs:
            save_detail_jobs(detail_jobs)

        print("✅ [수동 실행] 크롤링 및 DB 저장 완료")
    except Exception as e:
        print(f"❌ [수동 실행] 오류 발생: {e}")


if __name__ == "__main__":
    run()
