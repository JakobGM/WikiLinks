import pytest
import responses

from dataporten.tests.conftest import dataporten, dataporten_user
from dataporten.tests.utils import mock_usergroups_request
from dataporten.models import DataportenGroupManager
from dataporten.tests.factories import DataportenUserFactory
from .factories import (
        StudyProgramFactory,
        MainProfileFactory,
        SemesterFactory,
        CourseFactory,
        ResourceLinkListFactory,
        CourseLinkFactory,
        ResourceLinkFactory,
        ContributorFactory,
        OptionsFactory,
)

@pytest.fixture
def fysmat_user(dataporten_user, dataporten):
    """
    Dataporten user with courses given in dataporten.tests.groups.json
    """
    dataporten_user.dataporten = dataporten
    return dataporten_user

@pytest.fixture
def study_program():
    return StudyProgramFactory()

@pytest.fixture
def main_profile():
    return MainProfileFactory()

@pytest.fixture
def semester():
    return SemesterFactory()

@pytest.fixture
def course(semester):
    return CourseFactory(semesters=(semester,))

@pytest.fixture
def resource_link_list(study_program):
    return ResourceLinkListFactory(study_programs=(study_program,))

@pytest.fixture
def course_link():
    return CourseLinkFactory()

@pytest.fixture
def resource_link():
    return ResourceLinkFactory()

@pytest.fixture
def contributor():
    return ContributorFactory()

@pytest.fixture
def options():
    return OptionsFactory()
