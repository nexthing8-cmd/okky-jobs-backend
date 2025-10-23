-- 크롤링 히스토리 테이블 생성
CREATE TABLE crawling_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(20) NOT NULL,  -- 완료, 실패, 진행중
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP NULL,
    duration INT NULL,  -- 밀리초
    processed INT DEFAULT 0,  -- 처리된 항목 수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_crawling_history_started_at ON crawling_history(started_at);
CREATE INDEX idx_crawling_history_status ON crawling_history(status);
