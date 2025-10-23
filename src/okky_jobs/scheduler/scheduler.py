import sys
import os
import schedule
import time

print("✅ [시작] 스케줄러 컨테이너 진입")

# ✅ 프로젝트 루트 경로 추가 (패키지 인식 문제 해결)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ..crawler.crawler_master import crawl_all_master_jobs
from ..crawler.crawler_detail import crawl_detail_jobs
from ..db.db import save_master_jobs, save_detail_jobs

def job():
    print("\n=== [스케줄러] OKKY 전체 크롤링 시작 ===")
    try:
        master_jobs = crawl_all_master_jobs()

        if master_jobs:
            save_master_jobs(master_jobs)

        detail_jobs = crawl_detail_jobs(master_jobs)
        if detail_jobs:
            save_detail_jobs(detail_jobs)

        print("✅ [스케줄러] 크롤링 및 DB 저장 완료")
    except Exception as e:
        print(f"❌ [스케줄러] 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    print("✅ [__main__] 스케줄러 진입 및 초기 실행")
    job()  # 최초 1회 즉시 실행

    schedule.every().day.at("12:00").do(job)
    print("⏳ [스케줄러] 매일 12:00에 크롤링 실행 대기 중...")
    while True:
        schedule.run_pending()
        time.sleep(1)
