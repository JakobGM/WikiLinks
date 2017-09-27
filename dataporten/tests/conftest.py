""" Dataporten test settings and fixtures """

from django.contrib.auth.models import AnonymousUser, User
import pytest
import responses

from .factories import DataportenUserFactory, UserFactory
from .utils import mock_usergroups_request
from ..models import DataportenGroupManager
from ..parsers import Course


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

@pytest.fixture
def main_profile_json():
    return {
        "parent": "fc:org:ntnu.no",
        "displayName": "Industriell matematikk",
        "type": "fc:fs:str",
        "membership": {
            "displayName": "Student",
            "fsroles": [
                "STUDENT"
            ],
            "basic": "member",
            "active": True
        },
        "id": "fc:fs:fs:str:ntnu.no:MTFYMA-IM"
    }

@pytest.fixture
def organisation_unit_json():
    return {
        "displayName": "Seksjon for IT-brukerst\u00f8tte",
        "id": "fc:org:ntnu.no:unit:167500",
        "public": True,
        "parent": "fc:org:ntnu.no",
        "type": "fc:orgunit",
        "membership": {
            "primaryOrgUnit": True,
            "basic": "member"
        }
    }

@pytest.fixture
def finished_course():
    return Course(
        {
            "displayName": "Examen philosophicum for naturvitenskap og teknologi",
            "membership": {
                "notAfter": "2014-12-14T23:00:00Z",
                "active": True,
                "subjectRelations": "undervisning",
                "basic": "member",
                "fsroles": [
                    "STUDENT"
                ],
                "displayName": "Student"
            },
            "parent": "fc:org:ntnu.no",
            "url": "http://www.ntnu.no/exphil",
            "id": "fc:fs:fs:emne:ntnu.no:EXPH0004:1",
            "type": "fc:fs:emne",
        }
    )

@pytest.fixture
def non_finished_course():
    return Course(
        {
            "displayName": "Algebra ",
            "membership": {
                "basic": "member",
                "displayName": "Student",
                "active": True,
                "fsroles": [
                    "STUDENT"
                ]
            },
            "parent": "fc:org:ntnu.no",
            "url": "http://wiki.math.ntnu.no/tma4150",
            "id": "fc:fs:fs:emne:ntnu.no:TMA4150:1",
            "type": "fc:fs:emne"
        }
    )

@pytest.fixture
def ongoing_course():
    return Course(
        {
            "displayName": "Optimering I",
            "membership": {
                "notAfter": "2017-08-14T22:00:00Z",
                "active": True,
                "subjectRelations": "undervisning",
                "basic": "member",
                "fsroles": [
                    "STUDENT"
                ],
                "displayName": "Student"
            },
            "parent": "fc:org:ntnu.no",
            "url": "http://wiki.math.ntnu.no/tma4180",
            "id": "fc:fs:fs:emne:ntnu.no:TMA4180:1",
            "type": "fc:fs:emne"
        }
    )

@pytest.fixture
def course_last_semester():
	return Course(
		{
			"displayName": "Line\u00e6re metoder",
			"id": "fc:fs:fs:emne:ntnu.no:TMA4145:1",
			"parent": "fc:org:ntnu.no",
			"type": "fc:fs:emne",
			"membership": {
				"displayName": "Student",
				"notAfter": "2016-12-14T23:00:00Z",
				"active": True,
				"fsroles": [
					"STUDENT"
				],
				"subjectRelations": "undervisning",
				"basic": "member"
			},
			"url": "http://wiki.math.ntnu.no/tma4145"
		}
		)
