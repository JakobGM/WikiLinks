import requests

from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
from django.core.exceptions import SuspiciousOperation

from .provider import DataportenProvider


class DataportenAdapter(OAuth2Adapter):
    provider_id = DataportenProvider.id
    access_token_url = 'https://auth.dataporten.no/oauth/token'
    authorize_url = 'https://auth.dataporten.no/oauth/authorization'
    profile_url = 'https://auth.dataporten.no/userinfo'
    groups_url = 'https://groups-api.dataporten.no/groups/'
    redirect_uri_protocol = 'http'

    def complete_login(self, request, app, token, **kwargs):
        '''
        Arguments:
            request - The get request to the callback URL
                        /accounts/dataporten/login/callback with.
            app - The corresponding SocialApp model instance
            token - A token object with access token given in token.token
        Returns:
            Should return a dict with user information intended for parsing
            by the methods of the DataportenProvider view
        '''
        # The athentication header
        headers = {'Authorization': 'Bearer ' + token.token}

        # Userinfo endpoint, for documentation see:
        # https://docs.dataporten.no/docs/oauth-authentication/
        profile_data = requests.get(
            self.profile_url,
            headers=headers,
        )
        # Raise exception for 4xx and 5xx response codes
        profile_data.raise_for_status()

        # Groups endpoint, for documentation see:
        # https://docs.dataporten.no/docs/groups/
        groups_data = requests.get(
            self.groups_url + 'me/groups',
            headers=headers,
        )
        # Raise exception for 4xx and 5xx response codes
        groups_data.raise_for_status()

        extra_data = {
            'user': profile_data.json()['user'],
            'groups': groups_data.json(),
        }

        # Finally test that the audience property matches the client id
        # for validification reasons
        if profile_data.json()['audience'] != app.client_id:
            raise SuspiciousOperation(
                'Dataporten returned a user with an audience field \
                 which does not correspond to the client id of the \
                 application.'
                )

        return self.get_provider().sociallogin_from_response(
            request,
            extra_data,
        )


oauth_login = OAuth2LoginView.adapter_view(DataportenAdapter)
oauth_callback = OAuth2CallbackView.adapter_view(DataportenAdapter)
