# Admin Routes - All admin panel routes
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from services.auth_service import admin_required, log_admin_action, get_current_user
from services.admin_service import (
    get_dashboard_stats, get_all_settings, update_setting, toggle_feedback_window,
    create_feedback_period, get_all_feedback_periods, activate_feedback_period,
    deactivate_all_periods, get_all_students_with_eligibility, update_student_eligibility,
    bulk_update_eligibility, get_all_faculty, get_faculty_course_assignments,
    assign_faculty_to_course, remove_faculty_assignment, get_feedback_summary_by_faculty,
    get_feedback_details_by_faculty, get_recent_audit_logs, is_feedback_open,
    update_feedback_period, delete_feedback_period, get_feedback_period_by_id, auto_activate_scheduled_periods,
    close_feedback_period, open_feedback_period
)
from services.course_service import list_all_courses, create_course, get_all_courses_with_outcomes, add_course_outcome, delete_course_outcome
from services.faculty_service import add_faculty
from services.feedback_service import get_co_survey_summary

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ==================== DASHBOARD ====================

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    stats = get_dashboard_stats()
    return render_template('admin/dashboard.html', stats=stats)


# ==================== FEEDBACK WINDOW CONTROL ====================

@admin_bp.route('/feedback-control')
@admin_required
def feedback_control():
    """Feedback window control page"""
    settings = get_all_settings()
    periods = get_all_feedback_periods()
    current_time = datetime.now()
    return render_template('admin/feedback_control.html', settings=settings, periods=periods, current_time=current_time)


@admin_bp.route('/toggle-feedback', methods=['POST'])
@admin_required
def toggle_feedback():
    """Toggle feedback window open/close"""
    is_open = request.form.get('is_open') == 'true'
    admin_id = session.get('user_id')
    
    result = toggle_feedback_window(is_open, admin_id)
    
    if result['success']:
        log_admin_action(admin_id, f"{'Opened' if is_open else 'Closed'} feedback window", 'settings')
        flash(f"Feedback window {'opened' if is_open else 'closed'} successfully", 'success')
    else:
        flash(f"Failed to toggle feedback: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.feedback_control'))


@admin_bp.route('/create-period', methods=['POST'])
@admin_required
def create_period():
    """Create a new feedback period"""
    admin_id = session.get('user_id')
    
    period_name = request.form.get('period_name')
    academic_year = request.form.get('academic_year')
    semester = request.form.get('semester')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    feedback_type = request.form.get('feedback_type', 'both')
    
    result = create_feedback_period(period_name, academic_year, semester, start_date, end_date, feedback_type, admin_id)
    
    if result['success']:
        log_admin_action(admin_id, f"Created feedback period: {period_name}", 'feedback_period', result['period_id'])
        flash('Feedback period created successfully', 'success')
    else:
        flash(f"Failed to create period: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.feedback_control'))


@admin_bp.route('/activate-period/<int:period_id>', methods=['POST'])
@admin_required
def activate_period(period_id):
    """Activate a feedback period"""
    admin_id = session.get('user_id')
    
    result = activate_feedback_period(period_id, admin_id)
    
    if result['success']:
        log_admin_action(admin_id, f"Activated feedback period", 'feedback_period', period_id)
        flash('Feedback period activated', 'success')
    else:
        flash(f"Failed to activate period: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.feedback_control'))


@admin_bp.route('/deactivate-periods', methods=['POST'])
@admin_required
def deactivate_periods():
    """Deactivate all feedback periods"""
    admin_id = session.get('user_id')
    
    result = deactivate_all_periods(admin_id)
    
    if result['success']:
        log_admin_action(admin_id, "Deactivated all feedback periods", 'feedback_period')
        flash('All feedback periods deactivated', 'success')
    else:
        flash(f"Failed to deactivate: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.feedback_control'))


@admin_bp.route('/close-period/<int:period_id>', methods=['POST'])
@admin_required
def close_period(period_id):
    """Close a single feedback period"""
    admin_id = session.get('user_id')
    result = close_feedback_period(period_id, admin_id)
    if result['success']:
        log_admin_action(admin_id, f"Closed feedback period ID: {period_id}", 'feedback_period', period_id)
        flash('Feedback period closed successfully', 'success')
    else:
        flash(f"Failed to close period: {result.get('message')}", 'error')
    return redirect(url_for('admin.feedback_control'))


@admin_bp.route('/open-period/<int:period_id>', methods=['POST'])
@admin_required
def open_period(period_id):
    """Open/reopen a single feedback period"""
    admin_id = session.get('user_id')
    result = open_feedback_period(period_id, admin_id)
    if result['success']:
        log_admin_action(admin_id, f"Opened feedback period ID: {period_id}", 'feedback_period', period_id)
        flash('Feedback period opened successfully', 'success')
    else:
        flash(f"Failed to open period: {result.get('message')}", 'error')
    return redirect(url_for('admin.feedback_control'))


@admin_bp.route('/edit-period/<int:period_id>', methods=['POST'])
@admin_required
def edit_period(period_id):
    """Update an existing feedback period"""
    admin_id = session.get('user_id')
    
    period_name = request.form.get('period_name')
    academic_year = request.form.get('academic_year')
    semester = request.form.get('semester')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    feedback_type = request.form.get('feedback_type', 'both')
    
    result = update_feedback_period(period_id, period_name, academic_year, semester, start_date, end_date, feedback_type)
    
    if result['success']:
        log_admin_action(admin_id, f"Updated feedback period: {period_name}", 'feedback_period', period_id)
        flash('Feedback period updated successfully', 'success')
    else:
        flash(f"Failed to update period: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.feedback_control'))


@admin_bp.route('/delete-period/<int:period_id>', methods=['POST'])
@admin_required
def delete_period(period_id):
    """Delete a feedback period"""
    admin_id = session.get('user_id')
    
    result = delete_feedback_period(period_id)
    
    if result['success']:
        log_admin_action(admin_id, f"Deleted feedback period ID: {period_id}", 'feedback_period', period_id)
        flash('Feedback period deleted successfully', 'success')
    else:
        flash(f"Failed to delete: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.feedback_control'))


@admin_bp.route('/auto-activate-periods', methods=['POST'])
@admin_required
def auto_activate():
    """Manually trigger auto-activation of scheduled periods"""
    admin_id = session.get('user_id')
    result = auto_activate_scheduled_periods()
    
    if result['success']:
        log_admin_action(admin_id, "Triggered auto-activation of scheduled periods", 'feedback_period')
        flash('Periods auto-activated based on schedule', 'success')
    else:
        flash(f"Failed: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.feedback_control'))


# ==================== STUDENT ELIGIBILITY ====================

@admin_bp.route('/students')
@admin_required
def students():
    """Manage students and eligibility"""
    students = get_all_students_with_eligibility()
    return render_template('admin/students.html', students=students)


@admin_bp.route('/toggle-eligibility/<int:student_id>', methods=['POST'])
@admin_required
def toggle_eligibility(student_id):
    """Toggle student eligibility"""
    admin_id = session.get('user_id')
    is_eligible = request.form.get('is_eligible') == 'true'
    
    result = update_student_eligibility(student_id, is_eligible)
    
    if result['success']:
        log_admin_action(admin_id, f"{'Enabled' if is_eligible else 'Disabled'} student eligibility", 'student', student_id)
        flash('Student eligibility updated', 'success')
    else:
        flash(f"Failed to update: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.students'))


@admin_bp.route('/bulk-eligibility', methods=['POST'])
@admin_required
def bulk_eligibility():
    """Bulk update student eligibility"""
    admin_id = session.get('user_id')
    student_ids = request.form.getlist('student_ids')
    action = request.form.get('action')
    
    if not student_ids:
        flash('No students selected', 'warning')
        return redirect(url_for('admin.students'))
    
    is_eligible = action == 'enable'
    result = bulk_update_eligibility(student_ids, is_eligible)
    
    if result['success']:
        log_admin_action(admin_id, f"Bulk {'enabled' if is_eligible else 'disabled'} {result['affected']} students", 'student')
        flash(f"Updated eligibility for {result['affected']} students", 'success')
    else:
        flash(f"Failed to update: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.students'))


# ==================== FACULTY-COURSE ASSIGNMENT ====================

@admin_bp.route('/assignments')
@admin_required
def assignments():
    """Manage faculty-course assignments"""
    faculty = get_all_faculty()
    courses = list_all_courses()
    assignments = get_faculty_course_assignments()
    return render_template('admin/assignments.html', faculty=faculty, courses=courses, assignments=assignments)


@admin_bp.route('/assign-faculty', methods=['POST'])
@admin_required
def assign_faculty():
    """Assign faculty to course"""
    admin_id = session.get('user_id')
    
    faculty_id = request.form.get('faculty_id')
    course_id = request.form.get('course_id')
    academic_year = request.form.get('academic_year')
    semester = request.form.get('semester')
    section = request.form.get('section', 'A')
    
    result = assign_faculty_to_course(faculty_id, course_id, academic_year, semester, section, admin_id)
    
    if result['success']:
        log_admin_action(admin_id, f"Assigned faculty {faculty_id} to course {course_id}", 'assignment')
        flash('Faculty assigned to course successfully', 'success')
    else:
        flash(f"Failed to assign: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.assignments'))


@admin_bp.route('/remove-assignment/<int:assignment_id>', methods=['POST'])
@admin_required
def remove_assignment(assignment_id):
    """Remove faculty-course assignment"""
    admin_id = session.get('user_id')
    
    result = remove_faculty_assignment(assignment_id)
    
    if result['success']:
        log_admin_action(admin_id, f"Removed faculty assignment", 'assignment', assignment_id)
        flash('Assignment removed successfully', 'success')
    else:
        flash(f"Failed to remove: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.assignments'))


# ==================== COURSE MANAGEMENT ====================

@admin_bp.route('/courses')
@admin_required
def courses():
    """Manage courses with course outcomes"""
    courses = get_all_courses_with_outcomes()
    return render_template('admin/courses.html', courses=courses)


@admin_bp.route('/add-course', methods=['POST'])
@admin_required
def add_course():
    """Add a new course"""
    admin_id = session.get('user_id')
    
    course_name = request.form.get('course_name')
    course_code = request.form.get('course_code')
    department = request.form.get('department')
    semester = request.form.get('semester', 1)
    credits = request.form.get('credits', 3)
    
    result = create_course(course_name, course_code, department, int(semester), int(credits))
    
    if result['success']:
        log_admin_action(admin_id, f"Added course: {course_code}", 'course')
        flash('Course added successfully', 'success')
    else:
        flash(f"Failed to add course: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.courses'))


@admin_bp.route('/add-course-outcome', methods=['POST'])
@admin_required
def add_course_outcome_route():
    """Add a course outcome to a course"""
    admin_id = session.get('user_id')
    
    course_id = request.form.get('course_id')
    co_number = request.form.get('co_number')
    co_description = request.form.get('co_description')
    bloom_level = request.form.get('bloom_level')
    
    result = add_course_outcome(int(course_id), int(co_number), co_description, bloom_level or None)
    
    if result['success']:
        log_admin_action(admin_id, f"Added CO{co_number} to course ID {course_id}", 'course_outcome')
        flash(f'Course Outcome CO{co_number} added successfully', 'success')
    else:
        flash(f"Failed to add CO: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.courses'))


@admin_bp.route('/delete-course-outcome/<int:co_id>', methods=['POST'])
@admin_required
def delete_course_outcome_route(co_id):
    """Delete a course outcome"""
    admin_id = session.get('user_id')
    
    result = delete_course_outcome(co_id)
    
    if result['success']:
        log_admin_action(admin_id, f"Deleted course outcome ID {co_id}", 'course_outcome')
        flash('Course Outcome deleted successfully', 'success')
    else:
        flash(f"Failed to delete CO: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.courses'))


# ==================== FACULTY MANAGEMENT ====================

@admin_bp.route('/faculty')
@admin_required
def faculty():
    """Manage faculty"""
    faculty = get_all_faculty()
    return render_template('admin/faculty.html', faculty=faculty)


@admin_bp.route('/add-faculty', methods=['POST'])
@admin_required
def add_faculty_route():
    """Add a new faculty member"""
    admin_id = session.get('user_id')
    
    faculty_name = request.form.get('faculty_name')
    email = request.form.get('email')
    department = request.form.get('department')
    designation = request.form.get('designation')
    
    result = add_faculty(faculty_name, email, department, designation)
    
    if result['success']:
        log_admin_action(admin_id, f"Added faculty: {faculty_name}", 'faculty')
        flash('Faculty added successfully', 'success')
    else:
        flash(f"Failed to add faculty: {result.get('message')}", 'error')
    
    return redirect(url_for('admin.faculty'))


# ==================== REPORTS ====================

@admin_bp.route('/reports')
@admin_required
def reports():
    """View reports dashboard"""
    faculty_summary = get_feedback_summary_by_faculty()
    co_summary = get_co_survey_summary()
    return render_template('admin/reports.html', faculty_summary=faculty_summary, co_summary=co_summary)


@admin_bp.route('/faculty-report/<int:faculty_id>')
@admin_required
def faculty_report(faculty_id):
    """View detailed report for a faculty"""
    feedbacks = get_feedback_details_by_faculty(faculty_id)
    faculty = next((f for f in get_all_faculty() if f['faculty_id'] == faculty_id), None)
    return render_template('admin/faculty_report.html', feedbacks=feedbacks, faculty=faculty)


# ==================== AUDIT LOG ====================

@admin_bp.route('/audit-log')
@admin_required
def audit_log():
    """View audit log"""
    logs = get_recent_audit_logs(100)
    return render_template('admin/audit_log.html', logs=logs)


# ==================== API ENDPOINTS ====================

@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for dashboard stats"""
    return jsonify(get_dashboard_stats())


@admin_bp.route('/api/feedback-status')
@admin_required
def api_feedback_status():
    """API endpoint for feedback status"""
    return jsonify({'is_open': is_feedback_open()})
