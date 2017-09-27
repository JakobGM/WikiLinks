from django.contrib.auth.models import AnonymousUser

import pytest
import responses
from django.core.exceptions import ImproperlyConfigured
from freezegun import freeze_time

from .utils import mock_usergroups_request
from ..models import (
    DataportenGroupManager,
    CourseManager,
    DataportenUser,
)


@freeze_time('2016-01-01')
class TestDataportenGroupManager:
    def test_dataporten_courses(self, dataporten):
        # End time date in past
        assert 'EXPH0004' in dataporten.courses.finished
        assert 'EXPH0004' in dataporten.courses.all
        assert 'EXPH0004' not in dataporten.courses.active

        # End time date in future
        assert 'TMA4150' not in dataporten.courses.finished
        assert 'TMA4150' in dataporten.courses.all
        assert 'TMA4150' in dataporten.courses.active

        # No end time, implied future date
        assert 'TMA4180' not in dataporten.courses.finished
        assert 'TMA4180' in dataporten.courses.all
        assert 'TMA4180' in dataporten.courses.active

    def test_dataporten_study_program(self, dataporten):
        assert dataporten.study_programs[0].code == 'MTFYMA'

    def test_dataporten_main_profile(self, dataporten):
        assert dataporten.main_profiles[0].code == 'MTFYMA-IM'

    def test_dataporten_organisation_units(self, dataporten):
        assert dataporten.organisation_units[0].uid == 'fc:org:ntnu.no:unit:167500'
        assert dataporten.organisation_units[1].uid == 'fc:org:ntnu.no:unit:660000'


@freeze_time('2017-01-01')
class TestCourseManager:
    def test_less_semesters_ago(self, finished_course, course_last_semester, ongoing_course):
        courses = [
            finished_course,
            course_last_semester,
            ongoing_course,
        ]
        course_manager = CourseManager(courses)

        assert course_manager.less_semesters_ago(than=1) \
               == [ongoing_course.code]

        assert course_manager.less_semesters_ago(than=2) \
               == [course_last_semester.code, ongoing_course.code]

        assert course_manager.less_semesters_ago(than=20) \
               == [finished_course.code, course_last_semester.code, ongoing_course.code]

    @freeze_time('1900-01-01')
    def test_semester_in_future(self, ongoing_course):
        """
        The Course manager needs to behave correctly when it is presented with a course
        which ends in the next semester.
        """
        course_manager = CourseManager([ongoing_course])
        assert ongoing_course.code in course_manager.active


def token_import_function(user):
    return 'dummy_token_from_import_function'


class TestTokenImport:
    @pytest.mark.django_db
    def test_token_not_configured(self, settings, dataporten_user):
        try:
            del settings.DATAPORTEN_TOKEN_FUNCTION
        except AttributeError:
            pass

        with pytest.raises(ImproperlyConfigured) as excinfo:
            dataporten_user.token
        assert str(excinfo.value) == \
               'You need to define DATAPORTEN_TOKEN_FUNCTION in your ' \
               'settings.py'

    @pytest.mark.django_db
    def test_token_unimportable_path(self, settings, dataporten_user):
        settings.DATAPORTEN_TOKEN_FUNCTION = 'highly.unlikely.to.exist'

        with pytest.raises(ImproperlyConfigured) as excinfo:
            dataporten_user.token
        assert str(excinfo.value) == \
               'Could not import DATAPORTEN_TOKEN_FUNCTION with value ' \
               'highly.unlikely.to.exist'

    @pytest.mark.django_db
    def test_token_properly_configured(self, settings, dataporten_user):
        settings.DATAPORTEN_TOKEN_FUNCTION = \
            'dataporten.tests.test_models.token_import_function'

        assert dataporten_user.token == 'dummy_token_from_import_function'


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
