from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
import factory

from ..models import DataportenUser

# See the direct inspiration of these factories here:
# https://factoryboy.readthedocs.io/en/latest/recipes.html#example-django-s-profile


class SocialAccountFactory(factory.django.DjangoModelFactory):

    user = factory.SubFactory(
            'dataporten.tests.factories.DataportenUserFactory',
            social_account=None,
    )
    social_token = factory.RelatedFactory(
            'dataporten.tests.factories.SocialTokenFactory',
            'account',
    )
    provider = 'dataporten'

    class Meta:
        model = SocialAccount


class SocialAppFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SocialApp


class SocialTokenFactory(factory.django.DjangoModelFactory):
    token = 'dummy_token'
    account = factory.SubFactory(SocialAccountFactory, social_token=None)
    app = factory.SubFactory(SocialAppFactory)

    class Meta:
        model = SocialToken


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User


class DataportenUserFactory(factory.django.DjangoModelFactory):
    options = factory.RelatedFactory(
            'semesterpage.tests.factories.OptionsFactory',
            'user',
    )
    contributor = factory.RelatedFactory(
            'semesterpage.tests.factories.ContributorFactory',
            'user',
    )
    social_account = factory.RelatedFactory(SocialAccountFactory, 'user')

    class Meta:
        model = DataportenUser
