from collections import defaultdict
from typing import DefaultDict, List, Type, Tuple, Dict

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

from allauth.socialaccount.models import SocialToken
from defaultlist import defaultlist

from .api import usergroups
from .parsers import (
    BaseGroup,
    Course,
    PARSERS,
    Semester,
    group_factory,
)

class DataportenGroupManager:
    """
    A manager for all the different types of groups which dataporten provides.
    It gives access to the following properties:
        - courses
        - active_courses
        - inactive_courses
        - generic_groups
    """
    def __init__(self, token: str) -> None:
        # Fetch usergroups and insert into dictionary based on dataporten unique
        # id
        groups_json = usergroups(token)
        _all_groups = [group_factory(group_json) for group_json in groups_json]
        self.groups = {group.uid: group for group in _all_groups}

        # Make each group type NAME a direct property of the object itself,
        # each property containing a dictionary keyed on dataporten unique ids.
        for parser in PARSERS:
            setattr(self, parser.NAME, {})

        # Sort all groups into a dictionary keyed on the group type, uniquely
        # represented by the group type's NAME attribute.
        for uid, group in self.groups.items():
            getattr(self, group.NAME)[uid] = group

        self.courses = CourseManager(self.courses)  # type: ignore


class CourseManager:
    def __init__(self, courses: Dict[str, Course]) -> None:
        self.all = {course.code: course for course in courses.values()}
        self.semesters_ago: List[Tuple[int, str]] = []
        now = Semester.now()

        for course in courses.values():
            ago = now - course.semester
            self.semesters_ago.append((ago, course.code,))

    @property
    def active(self) -> List[str]:
        return [code for ago, code in self.semesters_ago if ago <= 0]

    @property
    def finished(self) -> List[str]:
        return [code for ago, code in self.semesters_ago if ago > 0]

    def less_semesters_ago(self, than) -> List[str]:
        return [code for ago, code in self.semesters_ago if ago < than]


class DataportenUser(User):
    """
    Adds a dataporten property to the user, which points to a
    DataportenGroupManager instance. This property is cached
    for the lifetime of the user instance, as the manager makes
    API requests to dataporten
    """

    class Meta:
        proxy = True

    @cached_property
    def token(self) -> str:
        try:
            token_func_path = settings.DATAPORTEN_TOKEN_FUNCTION
            token_func = import_string(token_func_path)
            return token_func(self)
        except ModuleNotFoundError:
            raise ImproperlyConfigured(
                f'Could not import DATAPORTEN_TOKEN_FUNCTION with value '
                f'{token_func_path}',
            )
        except AttributeError:
            raise ImproperlyConfigured(
                'You need to define DATAPORTEN_TOKEN_FUNCTION in your '
                'settings.py',
            )


    @cached_property
    def dataporten(self):
        return DataportenGroupManager(self.token)

    @staticmethod
    def valid_request(request: HttpRequest) -> bool:
        if hasattr(request, 'user') and request.user.is_authenticated:
            return SocialToken.objects.filter(
                account__user=request.user,
                account__provider='dataporten',
            ).exists()
        else:
            return False
