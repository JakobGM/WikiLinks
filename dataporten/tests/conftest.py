""" Dataporten test settings and fixtures """

from django.contrib.auth.models import AnonymousUser, User
import pytest
import responses

from .factories import DataportenUserFactory, UserFactory
from .utils import mock_usergroups_request
from ..models import DataportenGroupManager


@pytest.fixture
@responses.activate
def dataporten():
    group_json = mock_usergroups_request()
    return DataportenGroupManager('dummy_token')


@pytest.fixture
@pytest.mark.django_db
def dataporten_user():
    return DataportenUserFactory()


@pytest.fixture
@pytest.mark.django_db
def user_with_dataporten_token():
    """ A User which has not been swapped out with the proxy model """
    dp_user = DataportenUserFactory()
    dp_user.__class__ = User
    return dp_user
