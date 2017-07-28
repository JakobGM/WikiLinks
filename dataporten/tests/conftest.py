""" Dataporten test settings and fixtures """

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
def django_user():
    return UserFactory.build()
