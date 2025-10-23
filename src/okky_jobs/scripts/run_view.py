import sys
import os

# ✅ 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ..db.db import get_all_jobs, get_all_details
from ..utils.excel_utils import save_jobs_to_excel, save_details_to_excel

def main():
    print("=== OKKY JOBS 데이터 뷰어 ===")
    
    try:
        # 마스터 공고 조회
        print("\n1. 마스터 공고 조회 중...")
        jobs = get_all_jobs()
        print(f"총 {len(jobs)}건의 마스터 공고 조회됨")
        
        if jobs:
            print("📋 최근 5건의 마스터 공고:")
            for i, job in enumerate(jobs[:5]):
                print(f"  {i+1}. {job.title} - {job.company}")
            save_jobs_to_excel(jobs)
            print("📁 마스터 공고 엑셀 저장 완료")
        else:
            print("❌ 마스터 공고 데이터가 없습니다.")
        
        # 상세 공고 조회
        print("\n2. 상세 공고 조회 중...")
        details = get_all_details()
        print(f"총 {len(details)}건의 상세 공고 조회됨")
        
        if details:
            print("📋 최근 5건의 상세 공고:")
            for i, detail in enumerate(details[:5]):
                print(f"  {i+1}. {detail.link} - {detail.skill}")
            save_details_to_excel(details)
            print("📁 상세 공고 엑셀 저장 완료")
        else:
            print("❌ 상세 공고 데이터가 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()
