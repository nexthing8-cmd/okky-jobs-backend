CREATE TABLE okky_job_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    link VARCHAR(500) NOT NULL,
    registered_at VARCHAR(100),
    view_count INT DEFAULT 0,
    start_date VARCHAR(100),
    work_location VARCHAR(255),
    pay_date VARCHAR(50),
    skill VARCHAR(255),
    description TEXT,
    contact_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_link (link),
    CONSTRAINT fk_contact FOREIGN KEY (contact_id) REFERENCES okky_job_contacts(id) ON DELETE SET NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;