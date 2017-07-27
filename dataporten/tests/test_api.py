import json

import responses
from django.test import TestCase

from ..api import usergroups, userinfo
from .utils import mock_usergroups_request, mock_userinfo_request


class TestTypes(TestCase):
    """ Should hit type definitions in order to catch syntax errors """
    from ..api import GroupJSON


class TestUserInfo(TestCase):
    """ Test dataporten userinfo endpoint """

    @responses.activate
    def test_valid_case(self):
        userinfo_dict = mock_userinfo_request()
        userinfo_return = userinfo('testac')
        self.assertEqual(
            userinfo_return,
            userinfo_dict['user'],
        )


class TestGroups(TestCase):
    """ Test dataporten groups endpoint """

    @responses.activate
    def test_valid_case(self):
        groups_dict = mock_usergroups_request()
        userinfo_return = usergroups('testac')
        self.assertEqual(
            userinfo_return,
            groups_dict,
        )
