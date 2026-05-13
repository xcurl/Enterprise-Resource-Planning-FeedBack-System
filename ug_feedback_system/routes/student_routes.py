# Student Routes - Protected student functionality
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import student_required, eligible_student_required, get_current_user
from services.student_service import (
    get_student_dashboard_data, get_student_enrolled_courses, 
    enroll_student_in_course, get_courses_for_student_semester
)
from services.feedback_service import (
    get_available_feedback_targets, submit_faculty_feedback, 
    get_student_feedback_history, get_course_outcomes_for_student,
    submit_co_survey, get_student_co_survey_history
)
from services.admin_service import is_feedback_open, get_active_feedback_period, is_student_in_feedback_period, get_upcoming_periods_for_student, get_active_period_for_student
from config import CURRENT_ACADEMIC_YEAR, CURRENT_SEMESTER

student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.route('/dashboard')
@student_required
def dashboard():
    """Student dashboard"""
    student_id = session.get('user_id')
    data = get_student_dashboard_data(student_id)
    if data and data.get('student'):
        session['is_eligible'] = data['student'].get('is_eligible', session.get('is_eligible'))
    
    # Check if feedback is open specifically for this student's semester
    feedback_open = is_student_in_feedback_period(student_id)
    active_period = get_active_period_for_student(student_id)
    
    return render_template('student/dashboard.html', 
                         data=data, 
                         feedback_open=feedback_open,
                         active_period=active_period)


@student_bp.route('/my-courses')
@student_required
def my_courses():
    """View enrolled courses"""
    student_id = session.get('user_id')
    courses = get_student_enrolled_courses(student_id)
    # Get only courses available for student's semester
    available_courses = get_courses_for_student_semester(student_id)
    return render_template('student/my_courses.html', 
                         courses=courses, 
                         available_courses=available_courses)


@student_bp.route('/enroll-course', methods=['POST'])
@student_required
def enroll_course():
    """Enroll in a course"""
    student_id = session.get('user_id')
    course_id = request.form.get('course_id')
    
    if not course_id:
        flash('Please select a course to enroll', 'error')
        return redirect(url_for('student.my_courses'))
    
    result = enroll_student_in_course(student_id, course_id, CURRENT_ACADEMIC_YEAR)
    
    if result['success']:
        flash(result.get('message', 'Successfully enrolled in course'), 'success')
    else:
        flash(result.get('message', 'Failed to enroll'), 'error')
    
    return redirect(url_for('student.my_courses'))


# ==================== FACULTY FEEDBACK ====================

@student_bp.route('/faculty-feedback')
@eligible_student_required
def faculty_feedback():
    """Faculty feedback page"""
    student_id = session.get('user_id')
    
    if not is_feedback_open():
        # Show upcoming periods
        upcoming = get_upcoming_periods_for_student(student_id)
        if upcoming:
            next_period = upcoming[0]
            flash(f"Feedback submission is currently closed. Next period opens on {next_period['start_date'].strftime('%d %b %Y at %H:%M')}", 'warning')
        else:
            flash('Feedback submission is currently closed', 'warning')
        return redirect(url_for('student.dashboard'))
    
    # Check if student's semester matches the active feedback period
    if not is_student_in_feedback_period(student_id):
        upcoming = get_upcoming_periods_for_student(student_id)
        if upcoming:
            next_period = upcoming[0]
            flash(f"Feedback is not open for your semester at this time. Your next feedback period: {next_period['period_name']} ({next_period['start_date'].strftime('%d %b')} - {next_period['end_date'].strftime('%d %b %Y')})", 'info')
        else:
            flash('Feedback is not open for your semester at this time', 'warning')
        return redirect(url_for('student.dashboard'))
    
    targets = get_available_feedback_targets(student_id)
    
    return render_template('student/faculty_feedback.html', targets=targets)


@student_bp.route('/submit-faculty-feedback', methods=['POST'])
@eligible_student_required
def submit_faculty_feedback_route():
    """Submit faculty feedback"""
    if not is_feedback_open():
        flash('Feedback submission is currently closed', 'error')
        return redirect(url_for('student.dashboard'))
    
    student_id = session.get('user_id')
    
    # Check if student's semester matches the active feedback period
    if not is_student_in_feedback_period(student_id):
        flash('Feedback is not open for your semester at this time', 'error')
        return redirect(url_for('student.dashboard'))
    faculty_id = request.form.get('faculty_id')
    course_id = request.form.get('course_id')
    
    ratings = {
        'teaching_quality': int(request.form.get('teaching_quality', 3)),
        'communication': int(request.form.get('communication', 3)),
        'punctuality': int(request.form.get('punctuality', 3)),
        'subject_knowledge': int(request.form.get('subject_knowledge', 3)),
        'helping_nature': int(request.form.get('helping_nature', 3)),
        'overall_rating': int(request.form.get('overall_rating', 3))
    }
    
    comments = request.form.get('comments', '')
    is_anonymous = request.form.get('is_anonymous') == 'on'
    
    result = submit_faculty_feedback(student_id, faculty_id, course_id, ratings, comments, is_anonymous)
    
    if result['success']:
        flash('Feedback submitted successfully!', 'success')
    else:
        flash(f"Failed to submit: {result['message']}", 'error')
    
    return redirect(url_for('student.faculty_feedback'))


@student_bp.route('/feedback-history')
@student_required
def feedback_history():
    """View feedback history"""
    student_id = session.get('user_id')
    history = get_student_feedback_history(student_id)
    return render_template('student/feedback_history.html', history=history)


# ==================== COURSE OUTCOME SURVEY ====================

@student_bp.route('/co-survey')
@eligible_student_required
def co_survey():
    """Course outcome survey page"""
    if not is_feedback_open():
        flash('Survey submission is currently closed', 'warning')
        return redirect(url_for('student.dashboard'))
    
    student_id = session.get('user_id')
    
    # Check if student's semester matches the active feedback period
    if not is_student_in_feedback_period(student_id):
        flash('Survey is not open for your semester at this time', 'warning')
        return redirect(url_for('student.dashboard'))
    
    outcomes = get_course_outcomes_for_student(student_id)
    
    # Group by course
    courses = {}
    for co in outcomes:
        cid = co['course_id']
        if cid not in courses:
            courses[cid] = {
                'course_name': co['course_name'],
                'course_code': co['course_code'],
                'outcomes': []
            }
        courses[cid]['outcomes'].append(co)
    
    return render_template('student/co_survey.html', courses=courses)


@student_bp.route('/submit-co-survey', methods=['POST'])
@eligible_student_required
def submit_co_survey_route():
    """Submit course outcome survey"""
    if not is_feedback_open():
        flash('Survey submission is currently closed', 'error')
        return redirect(url_for('student.dashboard'))
    
    student_id = session.get('user_id')
    
    # Check if student's semester matches the active feedback period
    if not is_student_in_feedback_period(student_id):
        flash('Survey is not open for your semester at this time', 'error')
        return redirect(url_for('student.dashboard'))
    course_id = request.form.get('course_id')
    
    # Parse CO responses
    co_responses = {}
    for key, value in request.form.items():
        if key.startswith('co_level_'):
            co_id = key.replace('co_level_', '')
            comment_key = f'co_comment_{co_id}'
            co_responses[co_id] = {
                'level': int(value),
                'comment': request.form.get(comment_key, '')
            }
    
    result = submit_co_survey(student_id, course_id, co_responses)
    
    if result['success']:
        flash('Survey submitted successfully!', 'success')
    else:
        flash(f"Failed to submit: {result['message']}", 'error')
    
    return redirect(url_for('student.co_survey'))


@student_bp.route('/co-survey-history')
@student_required
def co_survey_history():
    """View CO survey history"""
    student_id = session.get('user_id')
    history = get_student_co_survey_history(student_id)
    return render_template('student/co_survey_history.html', history=history)


# ==================== LEGACY ROUTES (for backward compatibility) ====================

@student_bp.route('/students/register', methods=['POST'])
def register_student_route():
    """Legacy registration endpoint - redirect to proper registration"""
    flash('Please use the new registration form', 'info')
    return redirect(url_for('auth.register_page'))
