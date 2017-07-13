from datetime import datetime

from django.test import TestCase

from freezegun import freeze_time

from ..parsers import Course, Group, Membership, Semester, datetime_from

class TestDatetimeFrom(TestCase):
    def test_basic_correctness(self):
        dt = datetime_from('2017-08-14T22:00:01Z')
        self.assertEqual(
            [dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second],
            [2017, 8, 14, 22, 0, 1],
        )

class TestGroup(TestCase):
    study_program_json = {
        "displayName": "Fysikk og matematikk - masterstudium (5-årig)",
        "membership": {
            "basic": "member",
            "displayName": "Student",
            "active": True,
            "fsroles": [
                "STUDENT"
            ]
        },
        "parent": "fc:org:ntnu.no",
        "url": "http://www.ntnu.no/studier/mtfyma",
        "id": "fc:fs:fs:prg:ntnu.no:MTFYMA",
        "type": "fc:fs:prg",
    }
    def setUp(self):
        self.group_example = Group(self.study_program_json)

    def test_properties_present(self):
        self.assertEqual(
            self.group_example.name,
            'Fysikk og matematikk - masterstudium (5-årig)',
        )
        self.assertEqual(
            self.group_example.url,
            'http://www.ntnu.no/studier/mtfyma',
        )
        self.assertEqual(
            self.group_example.group_type,
            'prg',
        )

    def test_active_membership(self):
        self.assertTrue(self.group_example.membership)

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


@freeze_time('2016-01-01')
class TestCourse(TestCase):
    finished_course = Course(
        {
            "displayName": "Examen philosophicum for naturvitenskap og teknologi",
            "membership": {
                "notAfter": "2014-12-14T23:00:00Z",
                "active": True,
                "subjectRelations": "undervisning",
                "basic": "member",
                "fsroles": [
                    "STUDENT"
                ],
                "displayName": "Student"
            },
            "parent": "fc:org:ntnu.no",
            "url": "http://www.ntnu.no/exphil",
            "id": "fc:fs:fs:emne:ntnu.no:EXPH0004:1",
            "type": "fc:fs:emne",
        }
    )
    def test_course_code(self):
        self.assertEqual(
            self.finished_course.code,
            'EXPH0004',
        )

    def test_finished_course(self):
        self.assertFalse(self.finished_course.membership)


    def test_ongoing_course_with_end_time(self):
        ongoing_course = Course(
            {
                "displayName": "Optimering I",
                "membership": {
                    "notAfter": "2017-08-14T22:00:00Z",
                    "active": True,
                    "subjectRelations": "undervisning",
                    "basic": "member",
                    "fsroles": [
                        "STUDENT"
                    ],
                    "displayName": "Student"
                },
                "parent": "fc:org:ntnu.no",
                "url": "http://wiki.math.ntnu.no/tma4180",
                "id": "fc:fs:fs:emne:ntnu.no:TMA4180:1",
                "type": "fc:fs:emne"
            }
        )
        self.assertTrue(ongoing_course.membership)

    def test_ongoing_course_without_end_time(self):
        non_finished_course = Course(
            {
                "displayName": "Algebra ",
                "membership": {
                    "basic": "member",
                    "displayName": "Student",
                    "active": True,
                    "fsroles": [
                        "STUDENT"
                    ]
                },
                "parent": "fc:org:ntnu.no",
                "url": "http://wiki.math.ntnu.no/tma4150",
                "id": "fc:fs:fs:emne:ntnu.no:TMA4150:1",
                "type": "fc:fs:emne"
            }
        )
        self.assertTrue(non_finished_course.membership)


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
