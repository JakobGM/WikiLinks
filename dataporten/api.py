"""
Tools for gathering userinfo and groups for a specific dataporten user
"""
from typing import Any, Dict

import requests

USERINFO_URL = 'https://auth.dataporten.no/userinfo'
GROUPS_URL = 'https://groups-api.dataporten.no/groups/'


def userinfo(token: str) -> Dict[str, Any]:
    # The athentication header
    headers = {'Authorization': 'Bearer ' + token}

    # Userinfo endpoint, for documentation see:
    # https://docs.dataporten.no/docs/oauth-authentication/
    userinfo_response = requests.get(
        USERINFO_URL,
        headers=headers,
    )
    # Raise exception for 4xx and 5xx response codes
    userinfo_response.raise_for_status()

    # The endpoint returns json-data and it needs to be decoded
    return userinfo_response.json()['user']


def usergroups(token: str) -> Dict[str, Any]:
    # The athentication header
    headers = {'Authorization': 'Bearer ' + token}

    # Groups endpoint, for documentation see:
    # https://docs.dataporten.no/docs/groups/
    groups_data = requests.get(
        GROUPS_URL + 'me/groups',
        headers=headers,
    )
    # Raise exception for 4xx and 5xx response codes
    groups_data.raise_for_status()

    # The endpoint returns json-data and it needs to be decoded
    return groups_data.json()
