import json
from typing import Any, Dict, List

import responses

def mock_userinfo_request() -> Dict[str, Any]:
    """
    Mocks the next request to the userinfo dataporten endpoint.
    Returns the mocked response, but already json decoded
    """
    with open('dataporten/tests/userinfo.json') as userinfo_file:
        userinfo_dump = json.load(userinfo_file)

    responses.add(
        responses.GET,
        'https://auth.dataporten.no/userinfo',
        json=userinfo_dump,
        status=200,
    )

    return userinfo_dump


def mock_usergroups_request() -> List[Dict[Any, Any]]:
    """
    Mocks the next request to the groups dataporten endpoint.
    Returns the mocked response, but already json decoded
    """
    with open('dataporten/tests/groups.json') as groups_file:
        groups_dump = json.load(groups_file)

    responses.add(
        responses.GET,
        'https://groups-api.dataporten.no/groups/me/groups',
        json=groups_dump,
        status=200,
    )

    return groups_dump
