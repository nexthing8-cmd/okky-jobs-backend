#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
상세 공고 크롤링 테스트
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.okky_jobs.crawler.crawler_detail import crawl_detail_job
from src.okky_jobs.db.models import DetailJob

@unittest.skip("OKKY 모듈 테스트는 외부 의존성(Chrome, MySQL)으로 인해 스킵")
class TestDetailCrawling(unittest.TestCase):
    """상세 공고 크롤링 테스트 (스킵됨)"""
    
    def test_crawl_detail_job(self):
        """상세 공고 크롤링 테스트 (스킵됨)"""
        print("===== 상세 공고 크롤링 테스트 (스킵됨) =====")
        self.skipTest("OKKY 모듈 테스트는 외부 의존성으로 인해 스킵")

if __name__ == '__main__':
    unittest.main()