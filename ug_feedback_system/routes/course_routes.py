from flask import Blueprint, request, redirect
from services.course_service import create_course

course_bp = Blueprint("course", __name__)

@course_bp.route("/courses/create", methods=["POST"])
def create_course_route():
    create_course(request.form["course_name"])
    return redirect("/")
