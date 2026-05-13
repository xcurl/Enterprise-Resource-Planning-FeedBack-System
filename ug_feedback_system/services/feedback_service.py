# Business logic for feedback
from db.connection import get_db_connection
from services.admin_service import is_feedback_open, get_active_feedback_period


# ==================== FACULTY FEEDBACK ====================

def check_feedback_already_submitted(student_id, faculty_id, course_id, period_id=None):
    """Check if student has already submitted feedback for this faculty/course combination"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        if period_id:
            cursor.execute(
                """
                SELECT feedback_id FROM faculty_feedback 
                WHERE student_id = %s AND faculty_id = %s AND course_id = %s AND period_id = %s
                """,
                (student_id, faculty_id, course_id, period_id)
            )
        else:
            cursor.execute(
                """
                SELECT feedback_id FROM faculty_feedback 
                WHERE student_id = %s AND faculty_id = %s AND course_id = %s AND period_id IS NULL
                """,
                (student_id, faculty_id, course_id)
            )
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


def submit_faculty_feedback(student_id, faculty_id, course_id, ratings, comments, is_anonymous=True):
    """Submit faculty feedback with multiple rating criteria"""
    # Check if feedback window is open
    if not is_feedback_open():
        return {"success": False, "message": "Feedback submission is currently closed"}
    
    # Get active period
    period = get_active_feedback_period()
    period_id = period['period_id'] if period else None
    
    # Check for duplicate feedback
    if check_feedback_already_submitted(student_id, faculty_id, course_id, period_id):
        return {"success": False, "message": "You have already submitted feedback for this faculty-course combination"}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO faculty_feedback 
            (student_id, faculty_id, course_id, period_id, teaching_quality, communication, 
             punctuality, subject_knowledge, helping_nature, overall_rating, comments, is_anonymous)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (student_id, faculty_id, course_id, period_id, 
             ratings.get('teaching_quality'), ratings.get('communication'),
             ratings.get('punctuality'), ratings.get('subject_knowledge'),
             ratings.get('helping_nature'), ratings.get('overall_rating'),
             comments, is_anonymous)
        )
        conn.commit()
        return {"success": True, "message": "Feedback submitted successfully"}
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return {"success": False, "message": "You have already submitted feedback for this faculty-course combination"}
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def submit_student_feedback(student_id, faculty_id, rating, comments):
    """Legacy function for basic feedback (backward compatibility)"""
    return submit_faculty_feedback(
        student_id, faculty_id, None,
        {'overall_rating': rating, 'teaching_quality': rating, 'communication': rating,
         'punctuality': rating, 'subject_knowledge': rating, 'helping_nature': rating},
        comments
    )


def fetch_feedback_report():
    """Fetch all feedback for viewing"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 
            CASE WHEN ff.is_anonymous THEN 'Anonymous' ELSE s.student_name END as student_name,
            f.faculty_name,
            c.course_name,
            ff.teaching_quality,
            ff.communication,
            ff.punctuality,
            ff.subject_knowledge,
            ff.helping_nature,
            ff.overall_rating,
            ff.comments,
            ff.submitted_at
        FROM faculty_feedback ff
        JOIN students s ON ff.student_id = s.student_id
        JOIN faculty f ON ff.faculty_id = f.faculty_id
        LEFT JOIN courses c ON ff.course_id = c.course_id
        ORDER BY ff.submitted_at DESC
        """
    )

    report = cursor.fetchall()
    cursor.close()
    conn.close()
    return report


def get_student_feedback_history(student_id):
    """Get feedback history for a student"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT ff.*, f.faculty_name, c.course_name, c.course_code
            FROM faculty_feedback ff
            JOIN faculty f ON ff.faculty_id = f.faculty_id
            LEFT JOIN courses c ON ff.course_id = c.course_id
            WHERE ff.student_id = %s
            ORDER BY ff.submitted_at DESC
            """,
            (student_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_available_feedback_targets(student_id):
    """Get faculty-course combinations available for feedback from a student (filtered by section)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    period = get_active_feedback_period()
    period_id = period['period_id'] if period else None
    
    try:
        # Get student's enrolled courses and their assigned faculty (filtered by student's section)
        cursor.execute(
            """
            SELECT DISTINCT fca.faculty_id, fca.course_id, f.faculty_name, 
                   c.course_name, c.course_code, fca.section
            FROM student_enrollments se
            JOIN students s ON se.student_id = s.student_id
            JOIN faculty_course_assignments fca ON se.course_id = fca.course_id 
                AND fca.is_active = TRUE
                AND (fca.section = s.section OR fca.section IS NULL OR s.section IS NULL)
            JOIN faculty f ON fca.faculty_id = f.faculty_id AND f.is_active = TRUE
            JOIN courses c ON fca.course_id = c.course_id
            LEFT JOIN faculty_feedback ff ON ff.student_id = se.student_id 
                AND ff.faculty_id = fca.faculty_id 
                AND ff.course_id = fca.course_id
                AND (ff.period_id = %s OR (%s IS NULL AND ff.period_id IS NULL))
            WHERE se.student_id = %s AND se.is_active = TRUE AND ff.feedback_id IS NULL
            """,
            (period_id, period_id, student_id)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ==================== COURSE OUTCOME SURVEY ====================

def get_course_outcomes_for_student(student_id):
    """Get course outcomes for courses a student is enrolled in"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    period = get_active_feedback_period()
    period_id = period['period_id'] if period else None
    
    try:
        cursor.execute(
            """
            SELECT DISTINCT co.co_id, co.course_id, co.co_number, co.co_description, 
                   co.bloom_level, c.course_name, c.course_code
            FROM student_enrollments se
            JOIN courses c ON se.course_id = c.course_id
            JOIN course_outcomes co ON c.course_id = co.course_id
            LEFT JOIN course_outcome_survey cos ON cos.student_id = se.student_id 
                AND cos.co_id = co.co_id
                AND (cos.period_id = %s OR (%s IS NULL AND cos.period_id IS NULL))
            WHERE se.student_id = %s AND se.is_active = TRUE AND cos.survey_id IS NULL
            ORDER BY c.course_name, co.co_number
            """,
            (period_id, period_id, student_id)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def submit_co_survey(student_id, course_id, co_responses):
    """Submit course outcome survey responses"""
    # Check if feedback window is open
    if not is_feedback_open():
        return {"success": False, "message": "Survey submission is currently closed"}
    
    period = get_active_feedback_period()
    period_id = period['period_id'] if period else None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for co_id, data in co_responses.items():
            cursor.execute(
                """
                INSERT INTO course_outcome_survey 
                (student_id, course_id, co_id, period_id, attainment_level, comments)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE attainment_level = %s, comments = %s
                """,
                (student_id, course_id, co_id, period_id, data['level'], data.get('comment', ''),
                 data['level'], data.get('comment', ''))
            )
        conn.commit()
        return {"success": True, "message": "Survey submitted successfully"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_student_co_survey_history(student_id):
    """Get CO survey history for a student"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT cos.*, c.course_name, c.course_code, 
                   co.co_number, co.co_description
            FROM course_outcome_survey cos
            JOIN courses c ON cos.course_id = c.course_id
            JOIN course_outcomes co ON cos.co_id = co.co_id
            WHERE cos.student_id = %s
            ORDER BY cos.submitted_at DESC
            """,
            (student_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_co_survey_summary():
    """Get summary of CO survey results for admin reports"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT 
                c.course_id, c.course_name, c.course_code,
                co.co_id, co.co_number, co.co_description,
                COUNT(cos.survey_id) as response_count,
                COALESCE(ROUND(AVG(cos.attainment_level), 2), 0) as avg_attainment
            FROM courses c
            JOIN course_outcomes co ON c.course_id = co.course_id
            LEFT JOIN course_outcome_survey cos ON co.co_id = cos.co_id
            GROUP BY c.course_id, c.course_name, c.course_code, co.co_id, co.co_number, co.co_description
            HAVING COUNT(cos.survey_id) > 0
            ORDER BY c.course_name, co.co_number
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
