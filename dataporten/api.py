"""
Tools for gathering userinfo and groups for a specific dataporten user
"""
from typing import Any, Dict, List, Optional

import requests
from mypy_extensions import TypedDict


# All the required fields of the Dataporten
# JSON representation of groups memberships
class MembershipJSONBase(TypedDict):
    basic: str  # NOQA
    displayName: str
    active: bool
    fsroles: List[str]


# Optional fields
class MembershipJSON(MembershipJSONBase, total=False):
    notAfter: str
    subjectRelations: Optional[str]


# All the required fields of the Dataporten
# JSON representation of groups memberships
class GroupJSONBase(TypedDict):
    displayName: str
    parent: str
    url: str
    id: str
    type: str


# Optional fields
class GroupJSON(GroupJSONBase, total=False):
    membership: MembershipJSON


def userinfo(token: str) -> Dict[str, Any]:
    USERINFO_URL = 'https://auth.dataporten.no/userinfo'

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


def usergroups(token: str) -> List[GroupJSON]:
    GROUPS_URL = 'https://groups-api.dataporten.no/groups/'

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
