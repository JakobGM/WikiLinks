import datetime
from unittest.mock import Mock

from django.contrib.auth.models import Group, User
from django.test import TestCase

import pytest
from freezegun import freeze_time

from dataporten.models import DataportenUser
from dataporten.tests.factories import UserFactory
from ..apps import create_contributor_groups
from ..models import Course, Semester, norwegian_slugify
from .factories import (
        CourseFactory,
        CourseUploadFactory,
        MainProfileFactory,
        OptionsFactory,
        SemesterFactory,
        StudyProgramFactory,
)


class TestUser:
    @pytest.mark.django_db
    def test_new_user_permissions(self):
        create_contributor_groups()

        new_user = User.objects.create(username='provided_username')

        # Assert that the post_save signal listener has added the user.is_staff
        # permission, such that all user can have access to the admin back-end
        assert new_user.is_staff is True

        # All new users are added to the students group
        students_group = Group.objects.get(name='students')
        assert students_group in new_user.groups.all()

        # Assert that the contributor and options objects have been attached
        new_user.contributor
        new_user.options

    @pytest.mark.django_db
    def test_that_new_users_do_not_have_options_last_modified_attribute(self):
        user = UserFactory()
        assert user.options.last_user_modification is None

class TestStudyProgram:
    @pytest.mark.django_db
    def test_study_program_factory(self, study_program):
        assert study_program.display_name == 'Fysmat'

    @pytest.mark.django_db
    def test_slug_field(self):
        study_program = StudyProgramFactory(display_name='åøæ aoe åøæ')
        assert study_program.slug == 'aoe-aoe-aoe'


class TestMainProfile:
    @pytest.mark.django_db
    def test_main_profile_factory(self, main_profile):
        assert main_profile.display_name == 'InMat'

    @pytest.mark.django_db
    def test_slug_field(self):
        main_profile = MainProfileFactory(display_name='åøæ aoe åøæ')
        assert main_profile.slug == 'aoe-aoe-aoe'


class TestSemester:
    @pytest.mark.django_db
    def test_creation_of_semester_with_factory(self, semester):
        assert semester.number == 1
        assert semester.main_profile.display_name == 'InMat'

    @pytest.mark.django_db
    def test_simple_semester(self):
        simple_semester = SemesterFactory(
            study_program__display_name='fysmat',
            main_profile=None,
            number=1,
        )
        result = Semester.get(
            study_program='fysmat',
            number=1,
        )
        assert simple_semester == result

    @pytest.mark.django_db
    def test_main_profile_semester(self):
        main_profile_semester = SemesterFactory(
            study_program__display_name='fysmat',
            main_profile__display_name='indmat',
            number=1,
        )
        result = Semester.get(
            study_program='fysmat',
            main_profile='indmat',
            number=1,
        )
        assert main_profile_semester == result

    @pytest.mark.django_db
    def test_getting_lowest_semester_of_study_program(self):
        lowest_semester = SemesterFactory(
            study_program__display_name='fysmat',
            main_profile__display_name='indmat',
            number=2,
        )
        higher_semester = SemesterFactory(
            study_program=lowest_semester.study_program,
            main_profile=lowest_semester.main_profile,
            number=4,
        )
        result = Semester.get(
            study_program='fysmat',
        )
        assert lowest_semester == result

    @pytest.mark.django_db
    def test_alphabetical_ordering_when_several_lowest_semesters(self):
        alphabetical_first = SemesterFactory(
            study_program__display_name='fysmat',
            main_profile__display_name='indmat',
            number=2,
        )
        alphabetical_last = SemesterFactory(
            study_program=alphabetical_first.study_program,
            main_profile__display_name='tekfys',
            number=2,
        )
        result = Semester.get(
            study_program='fysmat',
        )
        assert alphabetical_first == result

    @pytest.mark.django_db
    def test_case_insensitive_search(self):
        semester = SemesterFactory(
            study_program__display_name='Fysmat',
        )
        result = Semester.get(
            study_program='FysMat',
        )
        assert semester == result

    @pytest.mark.django_db
    def test_lowest_main_profile_semester(self):
        even_lower_but_wrong = SemesterFactory(
            study_program__display_name='fysmat',
            main_profile=None,
            number=1,
        )
        lowest_semester = SemesterFactory(
            study_program=even_lower_but_wrong.study_program,
            main_profile__display_name='indmat',
            number=4,
        )
        highest = SemesterFactory(
            study_program=even_lower_but_wrong.study_program,
            main_profile=lowest_semester.main_profile,
            number=5,
        )
        result = Semester.get(
            study_program='fysmat',
            main_profile='indmat',
        )
        assert lowest_semester == result

    @pytest.mark.django_db
    def test_non_existing_semester(self):
        with pytest.raises(Semester.DoesNotExist):
            result = Semester.get(
                study_program='FysMat',
            )


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

    def test_course_url_property(self):
        course = CourseFactory.build(homepage='example.org')
        assert course.url == 'example.org'

        course.homepage = ''
        course.pk = 1
        assert course.url == '/oppdater/semesterpage/course/1/change/'


class TestCourseUpload:
    @pytest.mark.django_db
    def test_url(self):
        upload = CourseUploadFactory(course__course_code='TFY4200')
        assert upload.url == '/media/fagfiler/TFY4200/user_upload.pdf'

        # Need to delete the file in order to prevent collisions on the
        # file name during the next test run
        upload.file.delete()

    def test_filename(self):
        upload = CourseUploadFactory.build()
        assert upload.filename == 'user_upload.pdf'

    def test_str_representation(self):
        upload = CourseUploadFactory.build()
        assert str(upload) == 'user_upload.pdf'

        upload.display_name = 'user given name'
        assert str(upload) == 'user given name'


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

    @pytest.mark.django_db
    def test_last_user_modification(self):
        """
        Only direct user changes should update last_user_modification, not
        arbitrary code.
        """
        options = OptionsFactory(last_user_modification=None)
        options.save()
        assert options.last_user_modification == None


def test_norwegian_slugify():
    norwegian_phrase = 'aoe åøæ åøæ test'
    instance = Mock(display_name=norwegian_phrase)

    english_phrase = norwegian_slugify(instance)
    assert english_phrase == 'aoe aoe aoe test'
