import datetime
from typing import Dict, List, Optional, Tuple

from .api import GroupJSON, MembershipJSON


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

    for parser in PARSERS:
        if parser.valid(group):
            return parser(group)

    # In case somebody removed Group from PARSERS, this is a fall back group
    # which will accept all forms of dataporten groups
    return Group(group)


class BaseGroup:
    """
    A basic class for behaviour present in all Dataporten groups,
    intended for subclassing
    """

    DATAPORTEN_TYPE: Optional[str]
    NAME: str

    def __init__(self, group: GroupJSON) -> None:
        if not self.valid(group):
            raise TypeError('Invalid Group JSON structure')

        self.name = group.get('displayName', 'No display name').strip()
        self.url = group.get('url', '')
        self.uid = group['id']
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

    NAME = 'generic_groups'

    @classmethod
    def valid(cls, group: GroupJSON) -> bool:
        # No restrictions are imposed on the JSON for the fallback group as
        # long as the JSON passes through the __init__ method without
        # throwing exceptions
        return True


class Membership:
    def __init__(self, membership: MembershipJSON) -> None:
        if 'active' in membership:
            self.active = membership['active']
        else:
            # If there is no 'active' key, then the membership
            # is implicitly active (it seems)
            self.active = True

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


def next_holiday() -> datetime.datetime:
    now = datetime.datetime.now()
    if 1 <= now.month <= 6:
        return datetime.datetime(year=now.year, month=6, day=10)
    else:
        return datetime.datetime(year=now.year, month=12, day=22)


class Course(BaseGroup):
    DATAPORTEN_TYPE = 'emne'
    NAME = 'courses'

    def __init__(self, group: GroupJSON) -> None:
        super().__init__(group)
        self.code = group['id'].split(':')[-2]

        if self.membership is not None and self.membership.end_time:
            self.semester = Semester(self.membership.end_time)
        else:
            self.semester = Semester(next_holiday())

    CourseDict = Dict[str, 'Course']

    @classmethod
    def split_on_membership(
            cls,
            courses: List['Course'],
    ) -> Tuple[CourseDict, CourseDict]:

        """
        Return two dictionaries in a tuple (active, inactive,)
        of the form Dict[course_code] = course_object
        """

        active, inactive = {}, {}
        for course in courses:
            if course.membership:
                active[course.code] = course
            else:
                inactive[course.code] = course

        return active, inactive

class StudyProgram(BaseGroup):
    DATAPORTEN_TYPE = 'prg'
    NAME = 'study_programs'

    def __init__(self, group: GroupJSON) -> None:
        super().__init__(group)
        self.code = group['id'].split(':')[-1]


class MainProfile(BaseGroup):
    DATAPORTEN_TYPE = 'str'
    NAME = 'main_profiles'

    def __init__(self, group: GroupJSON) -> None:
        super().__init__(group)
        self.code = group['id'].split(':')[-1]


class OrganisationUnit(BaseGroup):
    DATAPORTEN_TYPE = 'orgunit'
    NAME = 'organisation_units'


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


PARSERS = [
    Course,
    StudyProgram,
    MainProfile,
    OrganisationUnit,
    Group,
]
