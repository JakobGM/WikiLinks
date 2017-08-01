from typing import Dict

from dataporten.parsers import Course as ParsedCourse

from .models import Course

def sync_dataporten_courses_with_db(courses: Dict[str, ParsedCourse]):
    # Course codes that the dataporten user has taken
    course_codes = courses.keys()

    # Intersection with course codes already registrered in the database
    already_in_database = Course.objects.\
            filter(course_code__in=course_codes).\
            values_list('course_code', flat=True)

    # Dataporten course codes that have not been found in the database
    missing_in_database = set(course_codes) - set(already_in_database)

    # Use the dataporten data in order to create new course model objects
    # for those course codes which have not been found in the database
    for key in missing_in_database:
        course = courses[key]
        Course.objects.create(
            full_name=course.name,
            homepage=course.url,
            course_code=course.code,
        )
