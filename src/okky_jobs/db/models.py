# okky_job/db/models.py

from typing import NamedTuple, Optional
from datetime import datetime

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

class DetailJob(NamedTuple):
    link: str
    registered_at: str
    view_count: int
    start_date: str
    work_location: str
    pay_date: str
    skill: str
    description: str
    contact_name: str
    contact_phone: str
    contact_email: str

class CrawlingLog(NamedTuple):
    id: Optional[int]
    type: str  # info, success, error, warning, progress
    message: str
    timestamp: datetime
    progress: Optional[int]  # 0-100
    created_at: datetime

class CrawlingHistory(NamedTuple):
    id: Optional[int]
    status: str  # 완료, 실패, 진행중
    started_at: datetime
    ended_at: Optional[datetime]
    duration: Optional[int]  # 밀리초
    processed: int
    created_at: datetime
