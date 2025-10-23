#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
상세 공고 조회 테스트
"""

import unittest
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

@unittest.skip("OKKY 모듈 테스트는 외부 의존성(Chrome, MySQL)으로 인해 스킵")
class TestViewDetail(unittest.TestCase):
    """상세 공고 조회 테스트 (스킵됨)"""
    
    def test_view_detail_by_link(self):
        """상세 공고 조회 테스트 (스킵됨)"""
        print("===== 상세 공고 조회 테스트 (스킵됨) =====")
        self.skipTest("OKKY 모듈 테스트는 외부 의존성으로 인해 스킵")

if __name__ == '__main__':
    unittest.main()