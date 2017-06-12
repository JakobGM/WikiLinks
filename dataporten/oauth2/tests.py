from allauth.socialaccount.tests import OAuth2TestsMixin
from allauth.tests import MockedResponse, TestCase

from .provider import DataportenProvider


class DataportenTest(OAuth2TestsMixin, TestCase):
    provider_id = DataportenProvider.id

    def get_login_response_json(self, with_refresh_token=True):
        # Dataporten does not send refresh tokens
        return '''{
            "access_token":"testac",
            "expires_in":3600,
            "scope": "userid profile groups"
        }'''

    def get_mocked_response(self):
        return MockedResponse(
            200,
            '''{
            "user": {
                "userid": "76a7a061-3c55-430d-8ee0-6f82ec42501f",
                "userid_sec": ["feide:andreas@uninett.no"],
                "name": "Andreas \u00c5kre Solberg",
                "email": "andreas.solberg@uninett.no",
                "profilephoto": "p:a3019954-902f-45a3-b4ee-bca7b48ab507"
            },
            "audience": "app123id"
            }'''
            )
