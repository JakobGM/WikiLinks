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


# Examples of json structures received from Dataporten representing groups
@pytest.fixture
def study_program_json():
    return {
        "displayName": "Fysikk og matematikk - masterstudium (5-årig)",
        "membership": {
            "basic": "member",
            "displayName": "Student",
            "active": True,
            "fsroles": [
                "STUDENT"
            ]
        },
        "parent": "fc:org:ntnu.no",
        "url": "http://www.ntnu.no/studier/mtfyma",
        "id": "fc:fs:fs:prg:ntnu.no:MTFYMA",
        "type": "fc:fs:prg",
    }

@pytest.fixture
def course_json():
    return {
        "displayName": "Examen philosophicum for naturvitenskap og teknologi",
        "id": "fc:fs:fs:emne:ntnu.no:EXPH0004:1",
        "parent": "fc:org:ntnu.no",
        "type": "fc:fs:emne",
        "membership": {
            "displayName": "Student",
            "notAfter": "2014-12-14T23:00:00Z",
            "active": True,
            "fsroles": [
                "STUDENT"
            ],
            "subjectRelations": "undervisning",
            "basic": "member"
        },
        "url": "http://www.ntnu.no/exphil"
    }

