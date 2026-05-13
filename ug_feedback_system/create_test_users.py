#!/usr/bin/env python3
"""
Script to create test users for the UG Feedback System
"""
import bcrypt
import sys
from db.connection import get_db_connection

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

def create_test_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Create admin user with password 'admin123'
    admin_hash = hash_password('admin123')
    print(f"Admin hash generated")
    
    try:
        # Update or insert admin
        cursor.execute(
            """
            INSERT INTO admins (username, email, password_hash, full_name, role)
            VALUES ('admin', 'admin@ugfeedback.edu', %s, 'System Administrator', 'super_admin')
            ON DUPLICATE KEY UPDATE password_hash = %s
            """,
            (admin_hash, admin_hash)
        )
        print("✅ Admin user created/updated (username: admin, password: admin123)")
        
        # Get branch_id for CS branch
        cursor.execute("SELECT branch_id FROM branches WHERE branch_code = 'CS' LIMIT 1")
        branch = cursor.fetchone()
        branch_id = branch['branch_id'] if branch else None
        
        if not branch_id:
            print("⚠️ No branches found - creating CS branch")
            cursor.execute(
                "INSERT INTO branches (branch_code, branch_name, department) VALUES ('CS', 'Computer Science & Engineering', 'Computer Science')"
            )
            branch_id = cursor.lastrowid
        
        # Create test student with password 'student123' - Year 3, Semester 5
        student_hash = hash_password('student123')
        cursor.execute(
            """
            INSERT INTO students (student_name, email, password_hash, usn, branch_id, year, semester)
            VALUES ('Test Student', 'student@test.com', %s, '1XX21CS001', %s, 3, 5)
            ON DUPLICATE KEY UPDATE password_hash = %s, branch_id = %s, year = 3, semester = 5
            """,
            (student_hash, branch_id, student_hash, branch_id)
        )
        print("✅ Test student created (email: student@test.com, password: student123, Sem 5)")
        
        # Get student_id
        cursor.execute("SELECT student_id FROM students WHERE usn = '1XX21CS001'")
        student = cursor.fetchone()
        student_id = student['student_id'] if student else None
        
        if student_id:
            # Enroll student in semester 5 courses only
            cursor.execute(
                """
                INSERT IGNORE INTO student_enrollments (student_id, course_id, academic_year, semester)
                SELECT %s, c.course_id, '2025-26', 5
                FROM courses c
                WHERE c.semester = 5
                """,
                (student_id,)
            )
            print("✅ Student enrolled in Semester 5 courses")
        
        # Create faculty-course assignments for semester 5
        cursor.execute(
            """
            INSERT IGNORE INTO faculty_course_assignments (faculty_id, course_id, academic_year, semester, section, assigned_by)
            SELECT f.faculty_id, c.course_id, '2025-26', 5, 'A', 1
            FROM faculty f
            CROSS JOIN courses c
            WHERE c.semester = 5
            LIMIT 10
            """
        )
        print("✅ Faculty-course assignments created for Sem 5")
        
        # Open feedback window
        cursor.execute(
            """
            UPDATE feedback_settings SET setting_value = 'true' WHERE setting_key = 'feedback_open'
            """
        )
        print("✅ Feedback window opened")
        
        conn.commit()
        print("\n✅ All test data created successfully!")
        print("\n--- Test Credentials ---")
        print("Admin: username=admin, password=admin123")
        print("Student: email=student@test.com, password=student123 (Sem 5)")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    sys.exit(0 if create_test_users() else 1)
