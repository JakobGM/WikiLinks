from django.test import TestCase
from django.urls import reverse, resolve
from .test_utils import populate_db

class TestSemesterURLResolver(TestCase):
    def setUp(self):
        self.models = populate_db()

    def test_simple_semester(self):
        simple_url = reverse(self.models['first_semester'])
        self.assertEqual(simple_url, '/fymat/1')
