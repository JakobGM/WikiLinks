import datetime
from typing import Dict, Any

def datetime_from(json_string: str) -> datetime.datetime:
        return datetime.datetime.strptime(
            json_string,
            '%Y-%m-%dT%H:%M:%SZ',
        )


class Group:
    def __init__(self, json_group: Dict[str, Any]) -> None:
        self.name = json_group.get('displayName', 'No display name')
        self.url = json_group.get('url', None)
        self.group_type = json_group['type'].split(':')[-1]

        if 'membership' in json_group:
            self.membership = Membership(json_group['membership'])
        else:
            self.membership = None


class Membership:
    def __init__(self, membership: Dict[str, Any]) -> None:
        self.active = membership['active']
        if 'notAfter' in membership:
            self.end_time = datetime_from(membership['notAfter'])
            self.semester = Semester(self.end_time)
        else:
            self.end_time = None

    def __bool__(self) -> bool:
        if not self.active:
            return False
        elif self.end_time is None:
            # If there is no mention of an end date, we can assume it to be true
            # This is often the case when there has not been set an examination
            # date yet
            return True
        else:
            return datetime.datetime.now() < self.end_time


class Course(Group):
    def __init__(self, json_group: Dict[str, Any]) -> None:
        super().__init__(json_group)

        # Assert that the group is in fact a course
        if self.group_type != 'emne':
            raise TypeError('Non-course group cast to Course')

        self.code = json_group['id'].split(':')[-2]


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

    @staticmethod
    def now():
        return Semester(datetime.datetime.now())

    def __sub__(self, other) -> int:
        return 2 * (self.year - other.year) + (self.season - other.season)
