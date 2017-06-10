from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class DataportenAccount(ProviderAccount):
    def get_avatar_url(self):
        '''
        Returns a valid URL to an 128x128 .png photo of the user
        '''
        # Documentation for user profile photos can be found here:
        # https://docs.dataporten.no/docs/oauth-authentication/
        base_url = 'https://api.dataporten.no/userinfo/v1/user/media/'
        return base_url + self.account.extra_data['profilephoto']

    def to_str(self):
        '''
        Returns string representation of a social account. Includes the name
        of the user.
        '''
        dflt = super(DataportenAccount, self).to_str()
        return '%s (%s)' % (
            self.account.extra_data.get('name', ''),
            dflt,
        )


class DataportenProvider(OAuth2Provider):
    id = 'dataporten'
    name = 'Dataporten'
    account_class = DataportenAccount

    def extract_uid(self, data):
        '''
        Returns the primary user identifier, an UUID string
        See: https://docs.dataporten.no/docs/userid/
        '''
        return data['user']['userid']

    def extract_common_fields(self, data):
        '''
        Returns the user fields which are saved to DataportenAccount.extra_data
        Documentation: https://docs.dataporten.no/docs/oauth-authentication/

        Typical return value:
        {
            "userid": "76a7a061-3c55-430d-8ee0-6f82ec42501f",
            "userid_sec": ["feide:andreas@uninett.no"],
            "name": "Andreas \u00c5kre Solberg",
            "email": "andreas.solberg@uninett.no",
            "profilephoto": "p:a3019954-902f-45a3-b4ee-bca7b48ab507"
        }
        '''
        return data['user']


provider_classes = [DataportenProvider]
