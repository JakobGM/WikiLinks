from django.contrib.auth.models import User

from allauth.socialaccount.models import SocialToken


def allauth_token(user: User) -> str:
    return SocialToken.objects.get(
        account__user=user,
        account__provider='dataporten',
    ).token
