import json

from django.test import TestCase

import responses

from ..api import userinfo, usergroups


class TestUserInfo(TestCase):
    """ Test dataporten userinfo endpoint """

    @responses.activate
    def test_valid_case(self):
        with open('dataporten/tests/userinfo.json') as userinfo_file:
            userinfo_dump = json.load(userinfo_file)

        responses.add(
            responses.GET,
            'https://auth.dataporten.no/userinfo',
            json=userinfo_dump,
            status=200,
        )

        userinfo_return = userinfo('testac')
        self.assertEqual(
            userinfo_return,
            userinfo_dump['user'],
        )


class TestGroups(TestCase):
    """ Test dataporten groups endpoint """

    @responses.activate
    def test_valid_case(self):
        with open('dataporten/tests/groups.json') as groups_file:
            groups_dump = json.load(groups_file)

        responses.add(
            responses.GET,
            'https://groups-api.dataporten.no/groups/me/groups',
            json=groups_dump,
            status=200,
        )

        userinfo_return = usergroups('testac')
        self.assertEqual(
            userinfo_return,
            groups_dump,
        )
