from allauth.socialaccount.providers.oauth.urls import default_urlpatterns
from .provider import DataportenProvider

urlpatterns = default_urlpatterns(DataportenProvider)
