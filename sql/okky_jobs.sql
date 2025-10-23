CREATE TABLE okky_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    link VARCHAR(500) NOT NULL,
    deadline VARCHAR(50),
    category VARCHAR(100),
    position VARCHAR(100),
    location VARCHAR(100),
    career VARCHAR(100),
    salary VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_link (link)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;