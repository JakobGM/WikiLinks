from django.contrib.auth.models import AnonymousUser, User

import pytest

from ..middleware import DataportenGroupsMiddleware
from ..models import DataportenUser


def test_dataporten_middleware_with_anonymous_user(rf):
    request = rf.get('')
    dpm = DataportenGroupsMiddleware(None)

    request.user = AnonymousUser()
    dpm.process_view(request)
    assert type(request.user) is AnonymousUser


@pytest.mark.django_db
def test_dataporten_middleware_with_plain_django_user(rf, django_user_model):
    request = rf.get('')
    dpm = DataportenGroupsMiddleware(None)

    request.user = django_user_model()
    dpm.process_view(request)
    assert type(request.user) is User


@pytest.mark.django_db
def test_dataporten_middleware_with_user_with_dataporten_credentials(rf, user_with_dataporten_token):
    request = rf.get('')
    dpm = DataportenGroupsMiddleware(None)

    request.user = user_with_dataporten_token
    dpm.process_view(request)
    assert type(request.user) is DataportenUser
