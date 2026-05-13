# Business logic for students
from db.connection import get_db_connection


def register_student(student_name, branch_id, year):
    """Legacy registration without auth"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO students (student_name, branch_id, year)
        VALUES (%s, %s, %s)
        """,
        (student_name, branch_id, year)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_all_students():
    """Get all students"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT s.*, b.branch_name, b.branch_code 
        FROM students s
        LEFT JOIN branches b ON s.branch_id = b.branch_id
        ORDER BY s.student_name
        """
    )
    students = cursor.fetchall()

    cursor.close()
    conn.close()
    return students


def get_student_enrolled_courses(student_id):
    """Get courses a student is enrolled in"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT c.*, se.semester as enrollment_semester, se.academic_year
            FROM student_enrollments se
            JOIN courses c ON se.course_id = c.course_id
            WHERE se.student_id = %s AND se.is_active = TRUE
            ORDER BY c.semester, c.course_name
            """,
            (student_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_courses_for_student_semester(student_id):
    """Get courses available for student's current semester (not yet enrolled)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get student's current semester
        cursor.execute(
            "SELECT semester FROM students WHERE student_id = %s",
            (student_id,)
        )
        student = cursor.fetchone()
        if not student:
            return []
        
        student_semester = student['semester']
        
        # Get courses for this semester that student is not already enrolled in
        cursor.execute(
            """
            SELECT c.* FROM courses c
            WHERE c.semester = %s
            AND c.course_id NOT IN (
                SELECT se.course_id FROM student_enrollments se 
                WHERE se.student_id = %s AND se.is_active = TRUE
            )
            ORDER BY c.course_code
            """,
            (student_semester, student_id)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def enroll_student_in_course(student_id, course_id, academic_year):
    """Enroll a student in a course (validates semester match)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get student's semester
        cursor.execute(
            "SELECT semester FROM students WHERE student_id = %s",
            (student_id,)
        )
        student = cursor.fetchone()
        if not student:
            return {"success": False, "message": "Student not found"}
        
        # Get course's semester
        cursor.execute(
            "SELECT semester, course_name FROM courses WHERE course_id = %s",
            (course_id,)
        )
        course = cursor.fetchone()
        if not course:
            return {"success": False, "message": "Course not found"}
        
        # Validate semester match
        if student['semester'] != course['semester']:
            return {
                "success": False, 
                "message": f"Cannot enroll in {course['course_name']}. This course is for semester {course['semester']}, but you are in semester {student['semester']}."
            }
        
        # Enroll the student
        cursor.execute(
            """
            INSERT INTO student_enrollments (student_id, course_id, academic_year, semester)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE is_active = TRUE
            """,
            (student_id, course_id, academic_year, student['semester'])
        )
        conn.commit()
        return {"success": True, "message": f"Successfully enrolled in {course['course_name']}"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_student_dashboard_data(student_id):
    """Get all data needed for student dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get student info with branch
        cursor.execute(
            """
            SELECT s.*, b.branch_name, b.branch_code
            FROM students s
            LEFT JOIN branches b ON s.branch_id = b.branch_id
            WHERE s.student_id = %s
            """,
            (student_id,)
        )
        student = cursor.fetchone()
        
        # Get enrolled courses count
        cursor.execute(
            "SELECT COUNT(*) as count FROM student_enrollments WHERE student_id = %s AND is_active = TRUE",
            (student_id,)
        )
        enrolled_courses = cursor.fetchone()['count']
        
        # Get feedback submitted count
        cursor.execute(
            "SELECT COUNT(*) as count FROM faculty_feedback WHERE student_id = %s",
            (student_id,)
        )
        feedbacks_submitted = cursor.fetchone()['count']
        
        # Get CO surveys submitted count
        cursor.execute(
            "SELECT COUNT(DISTINCT course_id) as count FROM course_outcome_survey WHERE student_id = %s",
            (student_id,)
        )
        co_surveys_submitted = cursor.fetchone()['count']
        
        return {
            'student': student,
            'enrolled_courses': enrolled_courses,
            'feedbacks_submitted': feedbacks_submitted,
            'co_surveys_submitted': co_surveys_submitted
        }
    finally:
        cursor.close()
        conn.close()
