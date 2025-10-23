#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
마스터 DB 저장 테스트
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.okky_jobs.crawler.crawler_master import crawl_all_master_jobs
from src.okky_jobs.db.db import save_master_jobs

@unittest.skip("OKKY 모듈 테스트는 외부 의존성(Chrome, MySQL)으로 인해 스킵")
class TestMasterDbSave(unittest.TestCase):
    """마스터 DB 저장 테스트 (스킵됨)"""
    
    def test_crawl_and_save_master_jobs(self):
        """마스터 공고 크롤링 및 DB 저장 테스트 (스킵됨)"""
        print("=== 마스터 DB 저장 테스트 (스킵됨) ===")
        self.skipTest("OKKY 모듈 테스트는 외부 의존성으로 인해 스킵")

if __name__ == '__main__':
    unittest.main()