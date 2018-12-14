from datetime import datetime

from django.test import TestCase
from freezegun import freeze_time

from ..parsers import (
        Course,
        Group,
        group_factory,
        MainProfile,
        Membership,
        OrganisationUnit,
        Semester,
        StudyProgram,
        datetime_from,
)


class TestDatetimeFrom(TestCase):
    def test_basic_correctness(self):
        dt = datetime_from('2017-08-14T22:00:01Z')
        self.assertEqual(
            [dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second],
            [2017, 8, 14, 22, 0, 1],
        )


class TestGroupFactory:
    def test_study_program_factory(self, study_program_json):
        study_program = next(group_factory(study_program_json))
        assert type(study_program) is StudyProgram

    def test_course_factory(self, course_json):
        course = next(group_factory(course_json))
        assert type(course) is Course

    def test_main_profile_factory(self, main_profile_json):
        main_profile = next(group_factory(main_profile_json))
        assert type(main_profile) is MainProfile

    def test_group_factory_given_iterable_argument(
            self,
            study_program_json,
            course_json,
    ):
        groups = group_factory(study_program_json, course_json)
        assert len(list(groups)) == 2


class TestGroup:
    def test_properties_present(self, study_program_json):
        group_example = Group(study_program_json)
        assert group_example.name == 'Fysikk og matematikk - masterstudium (5-årig)'
        assert group_example.url == 'http://www.ntnu.no/studier/mtfyma'
        assert group_example.group_type == 'prg'

    def test_active_membership(self, study_program_json):
        group_example = Group(study_program_json)
        assert group_example.membership


class TestMembership(TestCase):
    def test_perpetual_membership(self):
        unending_membership = Membership(
            {
                "basic": "member",
                "displayName": "Student",
                "active": True,
                "fsroles": [
                    "STUDENT"
                ]
            }
        )
        self.assertTrue(unending_membership)

    def test_inactive_membership(self):
        inactive_membership = Membership(
            {
                "basic": "member",
                "displayName": "Student",
                "active": False,
                "fsroles": [
                    "STUDENT"
                ]
            }
        )
        self.assertFalse(inactive_membership)

    @freeze_time('2017-08-13')
    def test_limited_membership(self):
        limited_membership = Membership(
            {
                "notAfter": "2017-08-14T22:00:00Z",
                "active": True,
                "subjectRelations": "undervisning",
                "basic": "member",
                "fsroles": [
                    "STUDENT"
                ],
                "displayName": "Student"
            }
        )
        self.assertTrue(limited_membership)

    @freeze_time('2017-08-15')
    def test_expired_membership(self):
        limited_membership = Membership(
            {
                "notAfter": "2017-08-14T22:00:00Z",
                "active": True,
                "subjectRelations": "undervisning",
                "basic": "member",
                "fsroles": [
                    "STUDENT"
                ],
                "displayName": "Student"
            }
        )
        self.assertFalse(limited_membership)


@freeze_time('2017-01-01')
class TestCourse:
    def test_course_code(self, finished_course):
        assert finished_course.code == 'EXPH0004'

    def test_finished_course(self, finished_course):
        assert not finished_course.membership
        assert finished_course.semester.year == 2014

    def test_ongoing_course_with_end_time(self, ongoing_course):
        assert ongoing_course.membership
        assert ongoing_course.semester.year == 2017

    @pytest.mark.xfail(strict=True, reason='Find out what causes this')
    def test_ongoing_course_without_end_time(self, non_finished_course):
        assert non_finished_course.membership
        assert non_finished_course.semester.year == 2017

    def test_split_on_membership(self, finished_course, non_finished_course, ongoing_course):
        courses = [
            finished_course,
            non_finished_course,
            ongoing_course,
        ]
        active, inactive = Course.split_on_membership(courses)

        assert finished_course.code in inactive.keys()
        assert finished_course in inactive.values()

        assert non_finished_course.code in active.keys()
        assert non_finished_course in active.values()

        assert ongoing_course.code in active.keys()
        assert ongoing_course in active.values()


class TestStudyProgram:
    def test_study_program_basic_properties(self, study_program_json):
        study_program = StudyProgram(study_program_json)
        assert study_program.code == 'MTFYMA'


class TestMainProfile:
    def test_main_profile_basic_properties(self, main_profile_json):
        main_profile = MainProfile(main_profile_json)
        assert main_profile.code == 'MTFYMA-IM'


class TestOrganisationUnit:
    def test_organisation_unit_basic_properties(self, organisation_unit_json):
        organisation_unit = OrganisationUnit(organisation_unit_json)
        assert organisation_unit.uid == 'fc:org:ntnu.no:unit:167500'


@freeze_time('2017-08-27')
class TestSemester(TestCase):
    def setUp(self):
        autumn_semester_date = datetime_from('2016-09-14T22:00:00Z')
        spring_semester_date = datetime_from('2016-04-04T22:00:00Z')

        self.autumn_semester = Semester(autumn_semester_date)
        self.spring_semester = Semester(spring_semester_date)
        self.present_semester = Semester.now()

    def test_year_of_semester(self):
        self.assertEqual(self.autumn_semester.year, 2016)
        self.assertEqual(self.present_semester.year, 2017)

    def test_semester_season(self):
        self.assertEqual(self.autumn_semester.season, Semester.AUTUMN)
        self.assertEqual(self.spring_semester.season, Semester.SPRING)

    def test_subtracting_semesters(self):
        same_semester_diff = self.present_semester - self.present_semester
        same_season_diff = self.present_semester - self.autumn_semester
        negative_diff = self.autumn_semester - self.present_semester
        different_season_diff = self.autumn_semester - self.spring_semester
        different_season_negative_diff = self.spring_semester - self.present_semester

        self.assertEqual(
            [same_semester_diff, same_season_diff, negative_diff, different_season_diff, different_season_negative_diff],
            [0, 2, -2, 1, -3],
        )
