import datetime
from unittest.mock import MagicMock

from django.contrib.auth.models import AnonymousUser, User

import pytest

from .factories import CourseFactory, SemesterFactory
from ..views import (
    homepage,
    profile,
    remove_course,
)
from dataporten.tests.factories import DataportenUserFactory

class TestProfileView:
    @pytest.mark.django_db
    def test_user_which_should_choose_their_courses(self, client, settings):
        settings.PICK_COURSES_ON_FIRST_LOGIN = True

        user = User.objects.create_user(username='olan', password='123')
        client.login(username='olan', password='123')
        response = client.get('/accounts/profile/', follow=True)
        assert response.redirect_chain == [(
            '/oppdater/semesterpage/options/1/change/',
            302,
        )]

    @pytest.mark.django_db
    def test_user_which_has_already_chosen_their_courses(self, client, settings):
        settings.PICK_COURSES_ON_FIRST_LOGIN = True

        user = User.objects.create_user(username='olan', password='123')
        user.options.last_user_modification = datetime.date.today()
        user.options.save()

        client.login(username='olan', password='123')
        response = client.get('/accounts/profile/', follow=True)
        assert response.redirect_chain == [('/olan/', 302)]

    @pytest.mark.django_db
    def test_not_choosing_courses_based_on_settings(self, client, settings):
        settings.PICK_COURSES_ON_FIRST_LOGIN = False
        user = User.objects.create_user(username='olan', password='123')

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

class TestRemoveCourseFromStudentPageView:
    @pytest.mark.django_db
    def test_course_is_removed(self):
        request = MagicMock()
        request.user.options.get_absolute_url.return_value = '/username/'
        user = DataportenUserFactory()
        request.user = user

        courses = CourseFactory.create_batch(2)
        request.user.options.self_chosen_courses = courses

        response = remove_course(request, courses[0].id)
        assert list(request.user.options.self_chosen_courses.all()) \
                 == courses[1:]
        assert response.url == '/username/'

    @pytest.mark.django_db
    def test_removing_course_requires_login(self, rf):
        request = rf.get('/fjern_fag/1/')
        request.user = AnonymousUser()

        response = remove_course(request, '1')
        assert response.status_code == 302
        assert response.url == '/accounts/dataporten/login?next=/fjern_fag/1/'

    @pytest.mark.django_db
    def test_remove_course_which_has_already_been_hidden(self):
        request = MagicMock()
        request.user.options.get_absolute_url.return_value = '/username/'
        user = DataportenUserFactory()
        request.user = user

        courses = CourseFactory.create_batch(2)
        request.user.options.self_chosen_courses = courses

        response = remove_course(request, '1000')
        assert list(request.user.options.self_chosen_courses.all()) == courses
        assert response.url == '/username/'
