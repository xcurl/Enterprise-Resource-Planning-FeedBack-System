# Define faculty routes here
from flask import Blueprint, request, redirect
from services.faculty_service import assign_faculty_to_course

faculty_bp = Blueprint("faculty", __name__)

@faculty_bp.route("/faculty/assign", methods=["POST"])
def assign_faculty_route():
    assign_faculty_to_course(
        request.form["faculty_name"],
        request.form["course_id"]
    )
    return redirect("/")
