import datetime
from typing import List, Optional

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


def datetime_from(json_string: str) -> datetime.datetime:
        return datetime.datetime.strptime(
            json_string,
            '%Y-%m-%dT%H:%M:%SZ',
        )


def group_type(group: GroupJSON) -> str:
    return group['type'].split(':')[-1]


def group_factory(group: GroupJSON) -> 'BaseGroup':

    """
    Given a JSON Group structure, this function returns the most specific
    object type, given the input
    """

    priorization = [Course]

    for kls in priorization:
        if kls.valid(group):
            return kls(group)

    return Group(group)


class BaseGroup:

    """
    A basic class for behaviour present in all Dataporten groups,
    intended for subclassing
    """

    DATAPORTEN_TYPE: Optional[str]

    def __init__(self, group: GroupJSON) -> None:
        if not self.valid(group):
            raise TypeError('Invalid Group JSON structure')

        self.name = group.get('displayName', 'No display name')
        self.url = group.get('url', None)
        self.group_type = group_type(group)

        if 'membership' in group:
            self.membership = Membership(group['membership'])
        else:
            self.membership = None

    @classmethod
    def valid(cls, group: GroupJSON) -> bool:
        """ Subclasses can define their corresponding Dataporten type """
        return cls.DATAPORTEN_TYPE == group_type(group)


class Group(BaseGroup):

    """ A fallback Group type """

    @classmethod
    def valid(cls, group: GroupJSON) -> bool:
        # No restrictions are imposed on the JSON for the fallback group as
        # long as the JSON passes through the __init__ method without
        # throwing exceptions
        return True


class Membership:
    def __init__(self, membership: MembershipJSON) -> None:
        self.active = membership['active']
        if 'notAfter' in membership:
            self.end_time = datetime_from(membership['notAfter'])
            self.semester = Semester(self.end_time)
        else:
            self.end_time = None

    def __bool__(self) -> bool:
        """
        The Membership object is truthy if the membership is not only active,
        but also current (old memberships stay active)
        """
        if not self.active:
            return False
        elif self.end_time is None:
            # If there is no end date, we can assume it to be true
            # This is often the case when there has not been set an examination
            # date yet
            return True
        else:
            return datetime.datetime.now() < self.end_time


class Course(BaseGroup):
    DATAPORTEN_TYPE = 'emne'
    def __init__(self, group: GroupJSON) -> None:
        super().__init__(group)
        self.code = group['id'].split(':')[-2]


class Semester:
    SPRING = 0
    AUTUMN = 1

    def __init__(self, dt: datetime.datetime) -> None:
        self.year = dt.year
        self.season = self.determine_season(dt.month)

    @classmethod
    def determine_season(cls, month: int) -> int:
        if 1 <= month <= 6:
            return cls.SPRING
        else:
            return cls.AUTUMN

    @classmethod
    def now(cls):
        return cls(datetime.datetime.now())

    def __sub__(self, other: 'Semester') -> int:
        return 2 * (self.year - other.year) + (self.season - other.season)
