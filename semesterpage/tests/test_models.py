from django.contrib.auth.models import Group, User
from django.test import TestCase

import pytest
from freezegun import freeze_time

from dataporten.models import DataportenUser
from ..apps import create_contributor_groups
from ..models import Course
from .factories import CourseFactory, SemesterFactory


class TestUser(TestCase):
    def setUp(self):
        create_contributor_groups()

    def test_new_user_permissions(self):
        new_user = User.objects.create(username='provided_username')

        # Assert that the post_save signal listener has added the user.is_staff
        # permission, such that all user can have access to the admin back-end
        self.assertIs(new_user.is_staff, True)

        # All new users are added to the students group
        students_group = Group.objects.get(name='students')
        self.assertIn(students_group, new_user.groups.all())

        # Assert that the contributor and options objects have been attached
        new_user.contributor
        new_user.options


class TestStudyProgram:
    @pytest.mark.django_db
    def test_study_program_factory(self, study_program):
        assert study_program.display_name == 'Fysmat'


class TestMainProfile:
    @pytest.mark.django_db
    def test_main_profile_factory(self, main_profile):
        assert main_profile.display_name == 'InMat'


class TestSemester:
    @pytest.mark.django_db
    def test_creation_of_semester_with_factory(self, semester):
        assert semester.number == 1
        assert semester.main_profile.display_name == 'InMat'


class TestCourse:
    @pytest.mark.django_db
    def test_creation_of_course_with_many_to_many_field(self, course):
        assert course.display_name == 'C++'
        assert course.semesters.all()[0].number == 1

    @pytest.mark.django_db
    def test_capitalize_course_code(self):
        course = CourseFactory.build()
        course.course_code = 'tma2422'
        course.save()
        assert course.course_code == 'TMA2422'

    def test_string_representation(self):
        course = Course(display_name='disp name given as a long string')
        assert course.short_name == 'disp name given as a long string'

        course = Course(full_name='nameshort')
        assert course.short_name == 'nameshort'

        course = Course(full_name='A very Long Course name but Acronymable')
        assert course.short_name == 'AVLCNBA'

        course = Course(full_name='Thisisanonacronymablelongcoursename')
        assert course.short_name == 'Thisisanona...'


class TestResourceLinkList:
    @pytest.mark.django_db
    def test_resource_link_list_factory_with_many_to_many_field(self, resource_link_list):
        assert resource_link_list.full_name == 'Ressurser'
        assert resource_link_list.study_programs.all()[0].display_name == 'Fysmat'


class TestCourseLink:
    @pytest.mark.django_db
    def test_basic_properties_of_course_link(self, course_link):
        assert course_link.url == 'http://ntnu.no/emne/TDT4102/'


class TestResourceLink:
    @pytest.mark.django_db
    def test_resource_link_factory(self, resource_link):
        assert resource_link.url == 'http://wolframalpha.com/'


@freeze_time('2017-05-27')
class TestContributor:
    @pytest.mark.django_db
    def test_contributor_factory(self, contributor):
        assert type(contributor.user) is DataportenUser
        assert contributor.access_level == 1

    @pytest.mark.django_db
    def test_dataporten_access(self, fysmat_user):
        """
        In this case, the user should be granted access to the
        courses entirely based on the contents of:
            dataporten.tests.groups.json
        """
        # Users do not have access to really old courses
        old_taken_course = CourseFactory(course_code='EXPH0004')
        assert not old_taken_course.check_access(fysmat_user)

        # This course is in the state of being taken,
        # thus access should be granted
        active_course = CourseFactory(
                full_name='unique name',
                course_code='TMA4180',
        )
        assert active_course.check_access(fysmat_user)

        # This course is from the previous semester,
        # and we grant access
        recent_course = CourseFactory(
                full_name='unique name 2',
                course_code='TMA4145',
        )
        assert active_course.check_access(fysmat_user)

        # This course does not even exist, and access
        # should not be granted
        non_taken_course = CourseFactory(
                full_name='unique name 3',
                course_code='XXX4200',
        )
        assert not non_taken_course.check_access(fysmat_user)



class TestOptions:
    @pytest.mark.django_db
    def test_options_factory(self, options):
        assert type(options.user) is DataportenUser
