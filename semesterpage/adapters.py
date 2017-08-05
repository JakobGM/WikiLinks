from typing import Dict

from django.db.models import Q

from dataporten.parsers import Course as ParsedCourse

from .models import Course
from dataporten.models import DataportenUser

def sync_dataporten_courses_with_db(courses: Dict[str, ParsedCourse]):
    # Course codes that the dataporten user has taken
    course_codes = courses.keys()

    # Intersection with course codes already registrered in the database
    already_in_database = Course.objects.\
            filter(course_code__in=course_codes)

    codes_already_in_database = already_in_database.\
            values_list('course_code', flat=True)

    # Dataporten course codes that have not been found in the database
    missing_in_database = set(course_codes) - set(codes_already_in_database)

    # Use the dataporten data in order to create new course model objects
    # for those course codes which have not been found in the database
    for key in missing_in_database:
        course = courses[key]
        Course.objects.create(
            full_name=course.name,
            homepage=course.url,
            course_code=course.code,
            dataporten_uid=course.uid,
        )

    # Populate pre-existing course model objects with dataporten uids
    missing_uid = already_in_database.filter(dataporten_uid=None)
    for course in missing_uid.all():
        course.dataporten_uid = courses[course.course_code].uid
        course.save(update_fields=['dataporten_uid'])

def sync_options_of_user_with_dataporten(user: DataportenUser) -> None:
    """
    Given a dataporten user, this function determines if the student
    has enrolled in any new courses since the last time, and if so
    adds the course(s) to their 'user.options.self_chosen_courses'.
    It also removes courses if the student has finished them.

    NB! This function assumes that all the courses provided from
    dataporten has already been persisted to the database as
    Course model instances. This can be done by invoking
    sync_dataporten_courses_with_db before invoking this function.
    """
    # The courses which the student is enrolled in, according to dataporten.
    active_dp_course = Q(course_code__in=user.dataporten.courses.active)

    # The courses which the student was enrolled in the last time this function
    # was called.
    saved_active_course = Q(pk__in=user.options.active_dataporten_courses.all())

    # We can now determine if there has been any changes to the set of active
    # courses provided by dataporten.
    new_active_courses = Course\
            .objects\
            .filter(active_dp_course)\
            .exclude(saved_active_course)

    new_finished_courses = Course\
            .objects\
            .filter(saved_active_course)\
            .exclude(active_dp_course)

    has_new_active_courses = new_active_courses.count() > 0
    has_new_finished_courses = new_finished_courses.count() > 0

    if has_new_active_courses:
        # Dataporten has provided new active courses from the last time we checked
        # this. We therefore update the user's 'self_chosen_courses'.
        user.options.self_chosen_courses.add(*new_active_courses.all())

    if has_new_finished_courses:
        # The student has recently finished courses, and we can remove the
        # courses from the student's homepage.
        user.options.self_chosen_courses.remove(*new_finished_courses.all())

    if has_new_active_courses or has_new_finished_courses:
        # Save the active courses for the next time we perform this check.
        active_dp_courses = Course.objects.filter(active_dp_course).all()
        user.options.active_dataporten_courses.set(active_dp_courses)
        user.options.save()
