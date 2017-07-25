from django.test import TestCase
from django.urls import resolve, reverse

from .test_utils import populate_db


class TestSemesterURLResolver(TestCase):
    def setUp(self):
        self.models = populate_db()

    def test_simple_semester(self):
        simple_url = reverse(
            'semesterpage-simplesemester',
            args=['fysmat', '1'],
        )
        self.assertEqual(simple_url, '/fysmat/1/')
