from collections import defaultdict
from typing import DefaultDict, List, Type

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils.functional import cached_property

from allauth.socialaccount.models import SocialToken

from .api import usergroups
from .parsers import Course, BaseGroup, group_factory

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

        self.active_courses, self.inactive_courses = \
                Course.split_on_membership(self.courses)


class DataportenUser(User):
    """
    Adds a dataporten property to the user, which points to a
    DataportenGroupManager instance. This property is cached
    for the lifetime of the user instance, as the manager makes
    API requests to dataporten
    """

    class Meta:
        proxy = True

    @property
    def token(self) -> str:
        return SocialToken.objects.get(
            account__user=self,
            account__provider='dataporten',
        ).token

    @cached_property
    def dataporten(self):
        return DataportenGroupManager(self.token)

    @classmethod
    def valid_request(cls, request: HttpRequest) -> bool:
        if hasattr(request, 'user') and request.user.is_authenticated():
            return SocialToken.objects.filter(
                account__user=request.user,
                account__provider='dataporten',
            ).exists()
        else:
            return False
