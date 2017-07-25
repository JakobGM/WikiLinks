from django.contrib.auth.models import Group, User
from django.test import TestCase

from ..apps import create_contributor_groups


class TestUser(TestCase):
    def setUp(self):
        create_contributor_groups()

    def test_new_user_permissions(self):
        new_user = User.objects.create(username='provided_username')

        # Assert that the post_save signal listener has added the user.is_staff
        # permission, such that all user can have access to the admin back-end
        self.assertIs(new_user.is_staff, True)

        # All new users are added to the students group
        students_group = Group.objects.get(name='students')
        self.assertIn(students_group, new_user.groups.all())

        # Assert that the contributor and options objects have been attached
        new_user.contributor
        new_user.options
