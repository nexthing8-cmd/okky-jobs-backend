from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, NamedTuple
import re, math, time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from ..utils.driver_utils import setup_driver
from ..utils.crawling_logger import CrawlingLogger

JOB_POST_LINK_SELECTOR = 'a[href^="/recruits/"]'
BASE_URL = "https://jobs.okky.kr/contract"

class MasterJob(NamedTuple):
    title: str
    company: str
    link: str
    deadline: str
    category: str
    position: str
    location: str
    career: str
    salary: str

def fetch_total_positions(soup: BeautifulSoup) -> int:
    span_tag = soup.select_one("div.sm\\:w-32 span.font-semibold")
    return int(span_tag.text.strip()) if span_tag else 0

def fetch_master_jobs(driver: webdriver.Chrome, url: str, is_first_page=False):
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, JOB_POST_LINK_SELECTOR))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        total_positions = fetch_total_positions(soup) if is_first_page else 0

        job_list = []
        post_links = soup.select(JOB_POST_LINK_SELECTOR)
        for link_tag in post_links:
            title_tag = link_tag.find("h2")
            if not title_tag:
                continue

            title = re.sub(r"\s+", " ", title_tag.text).strip()
            relative_link = link_tag["href"]
            full_link = urljoin(url, relative_link)

            company_tag = link_tag.select_one("span.text-gray-900.text-sm")
            company = company_tag.text.strip() if company_tag else ""

            deadline_tag = link_tag.select_one("span.bg-gray-500\\/70")
            deadline = deadline_tag.text.replace("마감", "").strip() if deadline_tag else ""

            category, position, location = "", "", ""
            info_div = link_tag.select_one("div.my-1.flex.gap-x-1")
            if info_div:
                smalls = [s.text.strip() for s in info_div.select("small") if "클린" not in s.text]
                if len(smalls) >= 1:
                    category = smalls[0]
                if len(smalls) >= 2:
                    position = smalls[1]
                if len(smalls) >= 3:
                    location = smalls[2]

            career, salary = "", ""
            spans = link_tag.select("div.mt-2.flex span")
            for s in spans:
                t = s.text.strip()
                if re.search(r"\d+년차|팀원|PL", t):
                    career = t
                if re.search(r"\d+~\d+만원|\d+만원", t):
                    salary = t

            job_list.append(MasterJob(
                title=title, company=company, link=full_link,
                deadline=deadline, category=category, position=position,
                location=location, career=career, salary=salary
            ))

        return job_list, total_positions

    except TimeoutException:
        print("❌ 마스터 페이지 로딩 시간 초과")
        return [], 0

def crawl_all_master_jobs() -> List[MasterJob]:
    logger = CrawlingLogger()
    history_id = logger.start_crawling_history()
    
    driver = setup_driver()
    all_jobs = []
    
    try:
        logger.log_info("크롤링 시작: OKKY 채용공고 수집")
        
        first_page_jobs, total_positions = fetch_master_jobs(driver, BASE_URL, is_first_page=True)
        all_jobs.extend(first_page_jobs)
        logger.log_info(f"첫 페이지에서 {len(first_page_jobs)}개 공고 수집")

        total_pages = math.ceil(total_positions / len(first_page_jobs)) if total_positions else 1
        logger.log_info(f"총 {total_pages} 페이지 순회 예정")

        for page in range(2, total_pages + 1):
            page_url = f"{BASE_URL}?page={page}"
            progress = int((page - 1) / total_pages * 100)
            logger.log_progress(f"페이지 {page}/{total_pages} 처리 중...", progress)
            
            jobs, _ = fetch_master_jobs(driver, page_url)
            all_jobs.extend(jobs)
            logger.log_info(f"페이지 {page}에서 {len(jobs)}개 공고 수집")
            
            # 진행률 업데이트
            logger.update_crawling_history("진행중", len(all_jobs))
            
            time.sleep(1)
            
    except Exception as e:
        logger.log_error(f"크롤링 중 오류 발생: {str(e)}")
        logger.update_crawling_history("실패", len(all_jobs))
        raise e
    finally:
        driver.quit()
        
        if history_id:
            logger.update_crawling_history("완료", len(all_jobs))
        
        logger.log_success(f"총 {len(all_jobs)}건 수집 완료")
        print(f"✅ 총 {len(all_jobs)}건 수집 완료")
    
    return all_jobs
