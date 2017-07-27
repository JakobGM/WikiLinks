import pytest

from .utils import mock_usergroups_request
from ..models import DataportenGroupManager
from ..tests.test_api import responses

@pytest.fixture
@responses.activate
def dataporten():
    group_json = mock_usergroups_request()
    return DataportenGroupManager('dummy_token')

def test_dataporten_courses(dataporten):
    assert 'EXPH0004' in dataporten.inactive_courses
    assert 'EXPH0004' not in dataporten.active_courses

    assert 'TMA4180' not in dataporten.inactive_courses
    assert 'TMA4180' in dataporten.active_courses

