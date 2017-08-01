import pytest

from ..adapters import sync_dataporten_courses_with_db
from ..models import Course
from .factories import CourseFactory
from dataporten.tests.conftest import (
    finished_course,
    non_finished_course,
    ongoing_course,
)

class TestSyncDataportenCoursesWithDB:
    @pytest.mark.django_db
    def test_basic_properties_of_saving_new_courses_to_db(
        self,
        finished_course,
        non_finished_course,
        ongoing_course,
        ):
        """
        Any dataporten courses that are not present in the database
        should be created by this function
        """
        db_courses = [finished_course, non_finished_course, ongoing_course]
        db_course_dict = {course.code: course for course in db_courses}
        CourseFactory(course_code=ongoing_course.code)

        # Before running the method, only one of the courses already exist
        assert Course.objects.filter(course_code__in=db_course_dict.keys()).count() == 1

        # After running the method, all the courses are persisted to the database
        sync_dataporten_courses_with_db(db_course_dict)
        assert Course.objects.filter(course_code__in=db_course_dict.keys()).count() == 3

        # Double-checking that all the available dataporten information has been
        # added to the new Course model instances
        algebra = Course.objects.get(course_code=non_finished_course.code)
        assert algebra.full_name == 'Algebra'
        assert algebra.homepage == 'http://wiki.math.ntnu.no/tma4150'
