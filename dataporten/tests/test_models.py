from django.contrib.auth.models import AnonymousUser

import pytest
import responses

from .utils import mock_usergroups_request
from ..models import DataportenGroupManager, DataportenUser


def test_dataporten_courses(dataporten):
    assert 'EXPH0004' in dataporten.inactive_courses
    assert 'EXPH0004' not in dataporten.active_courses

    assert 'TMA4180' not in dataporten.inactive_courses
    assert 'TMA4180' in dataporten.active_courses


@pytest.mark.django_db
def test_dataporten_user_token(dataporten_user):
    assert dataporten_user.token == 'dummy_token'


@pytest.mark.django_db
@responses.activate
def test_dataporten_user_groups(dataporten_user):
    group_json = mock_usergroups_request()
    groups = dataporten_user.dataporten
    assert isinstance(groups, DataportenGroupManager)


@pytest.mark.django_db
def test_dataporten_user_validation(rf, django_user_model, dataporten_user):
    # pytest-django provides a RequestFactory fixture named rf
    request = rf.get('')

    request.user = AnonymousUser()
    assert DataportenUser.valid_request(request) == False

    request.user = django_user_model()
    assert DataportenUser.valid_request(request) == False

    request.user = dataporten_user
    assert DataportenUser.valid_request(request) == True
