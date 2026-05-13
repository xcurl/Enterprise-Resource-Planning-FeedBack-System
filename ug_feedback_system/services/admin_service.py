# Admin Service - Business logic for admin controls
from db.connection import get_db_connection
from datetime import datetime
import json


# ==================== FEEDBACK WINDOW MANAGEMENT ====================

def get_all_settings():
    """Get all feedback settings"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM feedback_settings")
        settings = cursor.fetchall()
        return {s['setting_key']: s['setting_value'] for s in settings}
    finally:
        cursor.close()
        conn.close()


def update_setting(key, value, admin_id=None):
    """Update a feedback setting"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO feedback_settings (setting_key, setting_value, updated_by)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE setting_value = %s, updated_by = %s
            """,
            (key, value, admin_id, value, admin_id)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def is_feedback_open():
    """Check if any feedback period is currently active and not closed"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Period is open if: within date range AND not manually closed
        cursor.execute(
            """
            SELECT COUNT(*) as count FROM feedback_periods 
            WHERE NOW() BETWEEN start_date AND end_date 
            AND (is_closed = FALSE OR is_closed IS NULL)
            """
        )
        result = cursor.fetchone()
        return result['count'] > 0
    finally:
        cursor.close()
        conn.close()


def toggle_feedback_window(is_open, admin_id=None):
    """Open or close the feedback window"""
    return update_setting('feedback_open', 'true' if is_open else 'false', admin_id)


# ==================== FEEDBACK PERIODS ====================

def create_feedback_period(period_name, academic_year, semester, start_date, end_date, feedback_type, admin_id):
    """Create a new feedback period"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO feedback_periods (period_name, academic_year, semester, start_date, end_date, feedback_type, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (period_name, academic_year, semester, start_date, end_date, feedback_type, admin_id)
        )
        conn.commit()
        return {"success": True, "period_id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_all_feedback_periods():
    """Get all feedback periods"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT fp.*, a.full_name as created_by_name
            FROM feedback_periods fp
            LEFT JOIN admins a ON fp.created_by = a.admin_id
            ORDER BY fp.created_at DESC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_active_feedback_period():
    """Get currently active feedback period (within date range and not closed)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Period is active if: within date range AND not manually closed
        cursor.execute(
            """
            SELECT * FROM feedback_periods 
            WHERE NOW() BETWEEN start_date AND end_date 
            AND (is_closed = FALSE OR is_closed IS NULL)
            LIMIT 1
            """
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def is_student_in_feedback_period(student_id):
    """Check if student's semester has an active feedback period (within date range and not closed)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if there's an active period for student's semester
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM feedback_periods fp
            JOIN students s ON fp.semester = s.semester
            WHERE s.student_id = %s 
            AND NOW() BETWEEN fp.start_date AND fp.end_date
            AND (fp.is_closed = FALSE OR fp.is_closed IS NULL)
            """,
            (student_id,)
        )
        result = cursor.fetchone()
        return result['count'] > 0
    finally:
        cursor.close()
        conn.close()


def activate_feedback_period(period_id, admin_id):
    """Activate/Open a feedback period manually (clears is_closed flag)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get period details
        cursor.execute(
            "SELECT semester FROM feedback_periods WHERE period_id = %s",
            (period_id,)
        )
        period = cursor.fetchone()
        
        if not period:
            return {"success": False, "message": "Period not found"}
        
        # Clear is_closed flag to open the period
        cursor.execute(
            "UPDATE feedback_periods SET is_closed = FALSE WHERE period_id = %s",
            (period_id,)
        )
        conn.commit()
        
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def deactivate_all_periods(admin_id):
    """Deactivate all feedback periods"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE feedback_periods SET is_active = FALSE")
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def close_feedback_period(period_id, admin_id):
    """Close a specific feedback period (manual override)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Set is_closed = TRUE to manually close the period
        cursor.execute(
            "UPDATE feedback_periods SET is_closed = TRUE WHERE period_id = %s",
            (period_id,)
        )
        if cursor.rowcount == 0:
            conn.rollback()
            return {"success": False, "message": "Period not found"}
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def open_feedback_period(period_id, admin_id):
    """Open a specific feedback period (manual override - clear is_closed flag)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Set is_closed = FALSE to manually reopen the period
        cursor.execute(
            "UPDATE feedback_periods SET is_closed = FALSE WHERE period_id = %s",
            (period_id,)
        )
        if cursor.rowcount == 0:
            conn.rollback()
            return {"success": False, "message": "Period not found"}
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()
def auto_activate_scheduled_periods():
    """Auto-activate periods that are within their scheduled time (respects is_closed flag)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Note: We no longer auto-activate/deactivate based on is_active
        # The system now uses date range + is_closed flag for determining active status
        # This function can be used to reset is_closed for periods entering their window
        # But by default, we don't override manual closures
        
        # Just ensure is_active reflects current date status (for legacy compatibility)
        cursor.execute(
            """
            UPDATE feedback_periods 
            SET is_active = CASE 
                WHEN NOW() BETWEEN start_date AND end_date AND (is_closed = FALSE OR is_closed IS NULL) THEN TRUE
                ELSE FALSE
            END
            """
        )
        
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def update_feedback_period(period_id, period_name, academic_year, semester, start_date, end_date, feedback_type):
    """Update an existing feedback period"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            UPDATE feedback_periods 
            SET period_name = %s, academic_year = %s, semester = %s, 
                start_date = %s, end_date = %s, feedback_type = %s
            WHERE period_id = %s
            """,
            (period_name, academic_year, semester, start_date, end_date, feedback_type, period_id)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def delete_feedback_period(period_id):
    """Delete a feedback period"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if period has associated feedback
        cursor.execute(
            "SELECT COUNT(*) as count FROM faculty_feedback WHERE period_id = %s",
            (period_id,)
        )
        feedback_count = cursor.fetchone()[0]
        
        if feedback_count > 0:
            return {"success": False, "message": f"Cannot delete: {feedback_count} feedback responses are linked to this period"}
        
        cursor.execute("DELETE FROM feedback_periods WHERE period_id = %s", (period_id,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_feedback_period_by_id(period_id):
    """Get a specific feedback period by ID"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT * FROM feedback_periods WHERE period_id = %s",
            (period_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_upcoming_periods_for_student(student_id):
    """Get upcoming feedback periods for a student's semester"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT fp.* 
            FROM feedback_periods fp
            JOIN students s ON fp.semester = s.semester
            WHERE s.student_id = %s 
            AND fp.start_date > NOW()
            ORDER BY fp.start_date ASC
            LIMIT 3
            """,
            (student_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_active_period_for_student(student_id):
    """Get currently active feedback period for a specific student's semester"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT fp.* 
            FROM feedback_periods fp
            JOIN students s ON fp.semester = s.semester
            WHERE s.student_id = %s 
            AND NOW() BETWEEN fp.start_date AND fp.end_date 
            AND (fp.is_closed = FALSE OR fp.is_closed IS NULL)
            LIMIT 1
            """,
            (student_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# ==================== STUDENT ELIGIBILITY ====================

def get_all_students_with_eligibility():
    """Get all students with their eligibility status"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT s.student_id, s.student_name, s.email, s.usn, s.year, s.semester,
                   s.is_eligible, b.branch_name, b.branch_code
            FROM students s
            LEFT JOIN branches b ON s.branch_id = b.branch_id
            ORDER BY s.usn
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def update_student_eligibility(student_id, is_eligible):
    """Update a student's eligibility status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE students SET is_eligible = %s WHERE student_id = %s",
            (is_eligible, student_id)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def bulk_update_eligibility(student_ids, is_eligible):
    """Update eligibility for multiple students"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        placeholders = ','.join(['%s'] * len(student_ids))
        cursor.execute(
            f"UPDATE students SET is_eligible = %s WHERE student_id IN ({placeholders})",
            [is_eligible] + list(student_ids)
        )
        conn.commit()
        return {"success": True, "affected": cursor.rowcount}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


# ==================== FACULTY-COURSE ASSIGNMENT ====================

def get_all_faculty():
    """Get all faculty members"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT * FROM faculty WHERE is_active = TRUE ORDER BY faculty_name
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_faculty_course_assignments():
    """Get all faculty-course assignments"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT fca.*, f.faculty_name, f.department as faculty_dept, 
                   c.course_name, c.course_code
            FROM faculty_course_assignments fca
            JOIN faculty f ON fca.faculty_id = f.faculty_id
            JOIN courses c ON fca.course_id = c.course_id
            WHERE fca.is_active = TRUE
            ORDER BY fca.academic_year DESC, fca.semester DESC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def assign_faculty_to_course(faculty_id, course_id, academic_year, semester, section, admin_id):
    """Assign a faculty member to a course"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO faculty_course_assignments 
            (faculty_id, course_id, academic_year, semester, section, assigned_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE is_active = TRUE, assigned_by = %s
            """,
            (faculty_id, course_id, academic_year, semester, section, admin_id, admin_id)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def remove_faculty_assignment(assignment_id):
    """Remove a faculty-course assignment"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE faculty_course_assignments SET is_active = FALSE WHERE assignment_id = %s",
            (assignment_id,)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


# ==================== DASHBOARD STATISTICS ====================

def get_dashboard_stats():
    """Get statistics for admin dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        stats = {}
        
        # Total counts
        cursor.execute("SELECT COUNT(*) as count FROM students")
        stats['total_students'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM students WHERE is_eligible = TRUE")
        stats['eligible_students'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM faculty WHERE is_active = TRUE")
        stats['total_faculty'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM courses")
        stats['total_courses'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM faculty_feedback")
        stats['total_feedbacks'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM course_outcome_survey")
        stats['total_co_surveys'] = cursor.fetchone()['count']
        
        # Active period info
        active_period = get_active_feedback_period()
        stats['active_period'] = active_period
        stats['feedback_open'] = is_feedback_open()
        
        return stats
    finally:
        cursor.close()
        conn.close()


# ==================== REPORT ACCESS CONTROL ====================

def get_feedback_summary_by_faculty():
    """Get feedback summary grouped by faculty"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT 
                f.faculty_id,
                f.faculty_name,
                f.department,
                COUNT(ff.feedback_id) as feedback_count,
                ROUND(AVG(ff.teaching_quality), 2) as avg_teaching,
                ROUND(AVG(ff.communication), 2) as avg_communication,
                ROUND(AVG(ff.punctuality), 2) as avg_punctuality,
                ROUND(AVG(ff.subject_knowledge), 2) as avg_knowledge,
                ROUND(AVG(ff.helping_nature), 2) as avg_helping,
                ROUND(AVG(ff.overall_rating), 2) as avg_overall
            FROM faculty f
            LEFT JOIN faculty_feedback ff ON f.faculty_id = ff.faculty_id
            WHERE f.is_active = TRUE
            GROUP BY f.faculty_id
            ORDER BY avg_overall DESC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_feedback_details_by_faculty(faculty_id):
    """Get detailed feedback for a specific faculty"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT 
                ff.*,
                c.course_name, c.course_code,
                fp.period_name
            FROM faculty_feedback ff
            JOIN courses c ON ff.course_id = c.course_id
            LEFT JOIN feedback_periods fp ON ff.period_id = fp.period_id
            WHERE ff.faculty_id = %s
            ORDER BY ff.submitted_at DESC
            """,
            (faculty_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ==================== AUDIT LOG ====================

def get_recent_audit_logs(limit=50):
    """Get recent audit log entries"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT al.*, a.full_name as admin_name
            FROM audit_log al
            LEFT JOIN admins a ON al.admin_id = a.admin_id
            ORDER BY al.created_at DESC
            LIMIT %s
            """,
            (limit,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
