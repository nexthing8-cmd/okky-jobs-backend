-- 크롤링 로그 테이블 생성
CREATE TABLE crawling_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(20) NOT NULL,  -- info, success, error, warning, progress
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress INT DEFAULT NULL,  -- 진행률 (0-100)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_crawling_logs_timestamp ON crawling_logs(timestamp);
CREATE INDEX idx_crawling_logs_type ON crawling_logs(type);
