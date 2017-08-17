import datetime

from django.contrib.auth.models import User

import pytest

from ..views import profile
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
