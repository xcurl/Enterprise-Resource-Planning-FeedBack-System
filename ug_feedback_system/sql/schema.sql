-- UG Feedback System - Complete Database Schema

-- Courses Table (with semester mapping)
CREATE TABLE IF NOT EXISTS courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    course_code VARCHAR(20) UNIQUE,
    department VARCHAR(100),
    semester INT NOT NULL DEFAULT 1,
    credits INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Branches/Departments Table
CREATE TABLE IF NOT EXISTS branches (
    branch_id INT AUTO_INCREMENT PRIMARY KEY,
    branch_code VARCHAR(10) UNIQUE NOT NULL,
    branch_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students Table with Authentication
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    usn VARCHAR(20) UNIQUE NOT NULL,
    branch_id INT,
    year INT,
    semester INT,
    section VARCHAR(10),
    is_eligible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id) ON DELETE SET NULL
);

-- Admin Users Table
CREATE TABLE IF NOT EXISTS admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role ENUM('super_admin', 'admin', 'coordinator') DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Faculty Table
CREATE TABLE IF NOT EXISTS faculty (
    faculty_id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department VARCHAR(100),
    designation VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Faculty-Course Assignment (Many-to-Many)
CREATE TABLE IF NOT EXISTS faculty_course_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_id INT NOT NULL,
    course_id INT NOT NULL,
    academic_year VARCHAR(10),
    semester INT,
    section VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    assigned_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES admins(admin_id) ON DELETE SET NULL,
    UNIQUE KEY unique_assignment (faculty_id, course_id, academic_year, semester, section)
);

-- Feedback Window Settings
CREATE TABLE IF NOT EXISTS feedback_settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(50) UNIQUE NOT NULL,
    setting_value TEXT,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES admins(admin_id) ON DELETE SET NULL
);

-- Feedback Periods/Windows
CREATE TABLE IF NOT EXISTS feedback_periods (
    period_id INT AUTO_INCREMENT PRIMARY KEY,
    period_name VARCHAR(100) NOT NULL,
    academic_year VARCHAR(10),
    semester INT,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    is_closed BOOLEAN DEFAULT FALSE,
    feedback_type ENUM('faculty', 'course_outcome', 'both') DEFAULT 'both',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES admins(admin_id) ON DELETE SET NULL
);

-- Faculty Feedback (Student → Faculty)
CREATE TABLE IF NOT EXISTS faculty_feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    faculty_id INT NOT NULL,
    course_id INT NOT NULL,
    period_id INT,
    teaching_quality INT CHECK (teaching_quality BETWEEN 1 AND 5),
    communication INT CHECK (communication BETWEEN 1 AND 5),
    punctuality INT CHECK (punctuality BETWEEN 1 AND 5),
    subject_knowledge INT CHECK (subject_knowledge BETWEEN 1 AND 5),
    helping_nature INT CHECK (helping_nature BETWEEN 1 AND 5),
    overall_rating INT CHECK (overall_rating BETWEEN 1 AND 5),
    comments TEXT,
    is_anonymous BOOLEAN DEFAULT TRUE,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (period_id) REFERENCES feedback_periods(period_id) ON DELETE SET NULL,
    UNIQUE KEY one_feedback_per_student (student_id, faculty_id, course_id, period_id)
);

-- Course Outcomes
CREATE TABLE IF NOT EXISTS course_outcomes (
    co_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    co_number INT NOT NULL,
    co_description TEXT NOT NULL,
    bloom_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE KEY unique_co (course_id, co_number)
);

-- Course Outcome Survey (Student Response)
CREATE TABLE IF NOT EXISTS course_outcome_survey (
    survey_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    co_id INT NOT NULL,
    period_id INT,
    attainment_level INT CHECK (attainment_level BETWEEN 1 AND 5),
    comments TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (co_id) REFERENCES course_outcomes(co_id) ON DELETE CASCADE,
    FOREIGN KEY (period_id) REFERENCES feedback_periods(period_id) ON DELETE SET NULL,
    UNIQUE KEY one_survey_per_student_co (student_id, co_id, period_id)
);

-- Student Course Enrollment
CREATE TABLE IF NOT EXISTS student_enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    academic_year VARCHAR(10),
    semester INT,
    is_active BOOLEAN DEFAULT TRUE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, course_id, academic_year, semester)
);

-- Audit Log for Admin Actions
CREATE TABLE IF NOT EXISTS audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id) ON DELETE SET NULL
);



INSERT IGNORE INTO student_enrollments (student_id, course_id, academic_year, semester, is_active)
SELECT
    s.student_id,
    c.course_id,
    '2025-26',
    c.semester,
    TRUE
FROM students s
JOIN courses c ON c.course_code IN ('CS301', 'CS302')
WHERE s.email = 'student1@ugfeedback.edu';

-- Insert Default Settings
INSERT IGNORE INTO feedback_settings (setting_key, setting_value)
VALUES 
    ('feedback_open', 'false'),
    ('current_academic_year', '2025-26'),
    ('current_semester', '2'),
    ('allow_anonymous', 'true'),
    ('min_feedback_length', '10');

-- Sample Branches
INSERT IGNORE INTO branches (branch_code, branch_name, department)
VALUES 
    ('CS', 'Computer Science & Engineering', 'Computer Science'),
    ('IS', 'Information Science & Engineering', 'Information Science'),
    ('EC', 'Electronics & Communication', 'Electronics'),
    ('ME', 'Mechanical Engineering', 'Mechanical'),
    ('CV', 'Civil Engineering', 'Civil');

-- Sample Courses (with semester mapping)
INSERT IGNORE INTO courses (course_code, course_name, department, semester, credits)
VALUES 
    ('CS101', 'Introduction to Programming', 'Computer Science', 1, 4),
    ('MA101', 'Engineering Mathematics I', 'Mathematics', 1, 4),
    ('CS102', 'Computer Organization', 'Computer Science', 2, 4),
    ('MA102', 'Engineering Mathematics II', 'Mathematics', 2, 4),
    ('CS201', 'Data Structures', 'Computer Science', 3, 4),
    ('CS202', 'Discrete Mathematics', 'Computer Science', 3, 3),
    ('CS203', 'Object Oriented Programming', 'Computer Science', 4, 4),
    ('CS204', 'Computer Networks', 'Computer Science', 4, 3),
    ('CS301', 'Database Management Systems', 'Computer Science', 5, 4),
    ('CS302', 'Operating Systems', 'Computer Science', 5, 4),
    ('CS303', 'Web Technologies', 'Computer Science', 6, 3),
    ('CS304', 'Compiler Design', 'Computer Science', 6, 3),
    ('CS401', 'Software Engineering', 'Computer Science', 7, 3),
    ('CS402', 'Machine Learning', 'Computer Science', 7, 4),
    ('CS403', 'Cloud Computing', 'Computer Science', 8, 3),
    ('CS404', 'Capstone Project', 'Computer Science', 8, 6);

-- Sample Faculty
INSERT IGNORE INTO faculty (faculty_name, email, department, designation)
VALUES 
    ('Dr. John Smith', 'john.smith@ugfeedback.edu', 'Computer Science', 'Professor'),
    ('Prof. Sarah Wilson', 'sarah.wilson@ugfeedback.edu', 'Computer Science', 'Associate Professor'),
    ('Dr. Michael Brown', 'michael.brown@ugfeedback.edu', 'Computer Science', 'Assistant Professor'),
    ('Prof. Emily Davis', 'emily.davis@ugfeedback.edu', 'Mathematics', 'Professor');

-- Sample Course Outcomes for CS301 (DBMS - Semester 5)
INSERT IGNORE INTO course_outcomes (course_id, co_number, co_description, bloom_level)
SELECT c.course_id, co.co_number, co.co_description, co.bloom_level
FROM courses c
CROSS JOIN (
    SELECT 1 as co_number, 'Understand fundamental database concepts and ER modeling' as co_description, 'Understanding' as bloom_level
    UNION SELECT 2, 'Apply normalization techniques to design efficient databases', 'Applying'
    UNION SELECT 3, 'Write complex SQL queries for data manipulation', 'Applying'
    UNION SELECT 4, 'Analyze and optimize database performance', 'Analyzing'
) co
WHERE c.course_code = 'CS301'
ON DUPLICATE KEY UPDATE co_description = co.co_description;

-- Sample Course Outcomes for CS302 (OS - Semester 5)
INSERT IGNORE INTO course_outcomes (course_id, co_number, co_description, bloom_level)
SELECT c.course_id, co.co_number, co.co_description, co.bloom_level
FROM courses c
CROSS JOIN (
    SELECT 1 as co_number, 'Understand process management and scheduling algorithms' as co_description, 'Understanding' as bloom_level
    UNION SELECT 2, 'Apply memory management techniques', 'Applying'
    UNION SELECT 3, 'Analyze file system implementations', 'Analyzing'
    UNION SELECT 4, 'Design solutions for process synchronization', 'Creating'
) co
WHERE c.course_code = 'CS302'
ON DUPLICATE KEY UPDATE co_description = co.co_description;
