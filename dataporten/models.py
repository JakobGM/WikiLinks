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
from .parsers import Course, BaseGroup, group_factory, Semester

class DataportenGroupManager:
    """
    A manager for all the different types of groups which dataporten provides.
    It gives access to the following properties:
        - courses
        - active_courses
        - inactive_courses
        - generic_groups
    """
    courses: List[Course]

    def __init__(self, token: str) -> None:
        groups_json = usergroups(token)
        all_groups = [group_factory(group_json) for group_json in groups_json]
        categorized_groups: DefaultDict[str, List[BaseGroup]] = defaultdict(list)
        for group in all_groups:
            categorized_groups[group.NAME].append(group)

        for name, groups in categorized_groups.items():
            setattr(self, name, groups)

        # TODO: Here we should use the NullObject-pattern instead
        if not hasattr(self, 'courses'):
            self.courses = []

        self.courses = CourseManager(self.courses)  # type: ignore


class CourseManager:
    def __init__(self, courses: List[Course]) -> None:
        self.all = {course.code: course for course in courses}
        self.semesters_ago: List[Tuple[int, str]] = []
        now = Semester.now()

        for course in courses:
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
