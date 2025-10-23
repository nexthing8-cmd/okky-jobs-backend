from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import urljoin
from typing import List, Optional
import re, time, os

from .crawler_master import MasterJob
from ..db.models import DetailJob

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from ..utils.driver_utils import setup_driver

def extract_text_safe(element, default=""):
    return element.text.strip() if element else default

def crawl_detail_job(link: str) -> Optional[DetailJob]:
    driver = setup_driver()
    try:
        driver.get(link)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.mb-8.flex.flex-wrap"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        header_div = soup.select_one("div.mb-8.flex.flex-wrap")
        registered_at, view_count = "", 0
        if header_div:
            reg_span = header_div.select_one("span")
            registered_at = reg_span.text.strip() if reg_span else ""
            view_icon = header_div.select_one("div.flex.items-center.gap-x-0\\.5")
            if view_icon:
                view_text = view_icon.text.strip()
                view_count = int(re.sub(r"[^0-9]", "", view_text)) if view_text else 0

        start_date_tag = soup.find("div", string="근무시작일")
        start_date = extract_text_safe(start_date_tag.find_next("div")) if start_date_tag else ""

        work_location_tag = soup.find("div", string="근무지역")
        work_location = extract_text_safe(work_location_tag.find_next("div")) if work_location_tag else ""

        pay_date_tag = soup.find("div", string="급여지급일")
        pay_date = extract_text_safe(pay_date_tag.find_next("div")) if pay_date_tag else ""

        skill_tag = soup.find("div", string="보유스킬")
        skill = extract_text_safe(skill_tag.find_next("div")) if skill_tag else ""

        desc_container = soup.find("div", class_="my-5")
        description = ""
        if desc_container:
            paragraphs = [p.text.strip() for p in desc_container.find_all("p")]
            description = "\n".join([p for p in paragraphs if p])

        contact_div = soup.select_one("div.mb-9")
        contact_name, contact_phone, contact_email = "", "", ""
        if contact_div:
            items = contact_div.find_all("div", class_="flex items-center gap-x-3")
            if len(items) >= 1:
                contact_name = items[0].text.strip()
            if len(items) >= 2:
                contact_phone = items[1].text.strip()
            if len(items) >= 3:
                contact_email = items[2].text.strip()

        return DetailJob(
            link=link,
            registered_at=registered_at,
            view_count=view_count,
            start_date=start_date,
            work_location=work_location,
            pay_date=pay_date,
            skill=skill,
            description=description,
            contact_name=contact_name,
            contact_phone=contact_phone,
            contact_email=contact_email
        )

    except TimeoutException:
        print(f"❌ 상세 페이지 로딩 실패: {link}")
        return None
    finally:
        driver.quit()

def crawl_detail_jobs(master_jobs: List[MasterJob]) -> List[DetailJob]:
    detail_jobs = []
    for job in master_jobs:
        print(f"🔍 상세 크롤링 중: {job.title}")
        detail = crawl_detail_job(job.link)
        if detail:
            detail_jobs.append(detail)
        time.sleep(1)
    print(f"✅ 총 {len(detail_jobs)}건 상세 수집 완료")
    return detail_jobs
