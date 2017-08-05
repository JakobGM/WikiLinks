import pytest

from ..adapters import (
        sync_dataporten_courses_with_db,
        sync_options_of_user_with_dataporten,
)
from ..models import Course
from .factories import CourseFactory
from dataporten.tests.factories import DataportenUserFactory
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
        assert algebra.dataporten_uid == 'fc:fs:fs:emne:ntnu.no:TMA4150:1'

class TestSyncOptionsOfUserWithDataporten:
    @pytest.mark.django_db
    def test_new_user(self):
        dp_user = DataportenUserFactory()
        sync_dataporten_courses_with_db(dp_user.dataporten.courses.all)

        # The user has no self chosen courses (scc) before the sync process
        assert dp_user.options.self_chosen_courses.count() == 0

        sync_options_of_user_with_dataporten(dp_user)

        # After the sync, all the active courses have been added to the scc
        assert len(dp_user.dataporten.courses.active) == dp_user.options.self_chosen_courses.count()

    @pytest.mark.django_db
    def test_user_has_removed_one_of_the_self_chosen_courses(self):
        dp_user = DataportenUserFactory()
        sync_dataporten_courses_with_db(dp_user.dataporten.courses.all)
        sync_options_of_user_with_dataporten(dp_user)
        course = dp_user.options.self_chosen_courses.all()[0]

        # The user removes one of the scc's
        dp_user.options.self_chosen_courses.remove(course)
        dp_user.options.save()
        dp_user.refresh_from_db()

        count_before = dp_user.options.self_chosen_courses.count()
        sync_options_of_user_with_dataporten(dp_user)

        # The sync process should not remove something the user has removed
        # by purpose.
        assert dp_user.options.self_chosen_courses.count() == count_before
        assert count_before == len(dp_user.dataporten.courses.active) - 1

    @pytest.mark.django_db
    def test_user_has_finished_a_course_since_last_time(self):
        # TODO: I need to learn some heavy mocking before I can write this test
        assert True
