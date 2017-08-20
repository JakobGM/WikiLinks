import datetime
from unittest.mock import MagicMock

from django.contrib.auth.models import User

import pytest

from .factories import CourseFactory, SemesterFactory
from ..views import homepage, profile
from dataporten.tests.factories import DataportenUserFactory

class TestProfileView:
    @pytest.mark.django_db
    def test_user_which_should_choose_their_courses(self, client):
        user = User.objects.create_user(username='olan', password='123')
        client.login(username='olan', password='123')
        response = client.get('/accounts/profile/', follow=True)
        assert response.redirect_chain == [(
            '/oppdater/semesterpage/options/1/change/',
            302,
        )]

    @pytest.mark.django_db
    def test_user_which_has_already_chosen_their_courses(self, client):
        user = User.objects.create_user(username='olan', password='123')
        user.options.last_user_modification = datetime.date.today()
        user.options.save()

        client.login(username='olan', password='123')
        response = client.get('/accounts/profile/', follow=True)
        assert response.redirect_chain == [('/olan/', 302)]

class TestAdminModelHistory:
    @pytest.mark.django_db
    def test_non_superuser_being_refused_access(self, client):
        User.objects.create_user(
            username='olan',
            password='123',
            is_staff=True,
        )
        client.login(username='olan', password='123')
        response = client.get('/oppdater/semesterpage/course/1/history/')
        assert response.status_code == 302
        assert response.url == '/'


    @pytest.mark.django_db
    def test_superuser_being_given_history_access(self, client):
        User.objects.create_user(
            username='olan',
            password='123',
            is_superuser=True,
        )
        client.login(username='olan', password='123')
        CourseFactory(pk=1)
        response = client.get('/oppdater/semesterpage/course/1/history/')
        assert response.status_code == 200


class TestHomepageView:
    @pytest.mark.django_db
    def test_logged_in_user_visiting_homepage(self, client):
        """
        The user is authenticated, and should be redirected to their homepage.
        """
        User.objects.create_user(
            username='olan',
            password='123',
        )
        client.login(username='olan', password='123')

        response = client.get('/', follow=True)
        assert response.redirect_chain == [(
            '/olan/',
            302,
        )]

    @pytest.mark.django_db
    def test_user_with_old_visit_to_student_page(self, rf):
        """
        The user has a saved homepage, and can be redirected without logging in.
        """
        request = MagicMock()
        request.user.is_authenticated = False
        request.session = {'homepage': 'username'}

        response = homepage(request)
        assert response.url == '/username/'

    @pytest.mark.django_db
    def test_user_with_old_visit_to_semester(self, rf):
        """
        The user has visited a semester before, and can be redirected.
        """
        semester = SemesterFactory(
            pk=1,
            study_program__display_name='fysmat',
            main_profile=None,
            number=1,
        )
        request = MagicMock()
        request.user.is_authenticated = False
        request.session = {'semester_pk': 1}
        response = homepage(request)
        assert response.url == '/fysmat/1/'
