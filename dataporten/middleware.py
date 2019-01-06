import requests_cache
from django.conf import settings
from django.http import HttpRequest

from .models import DataportenUser

# Cache requests for 15 minutes
if settings.DATAPORTEN_CACHE_REQUESTS:
    requests_cache.install_cache(
        settings.DATAPORTEN_CACHE_PATH + 'dataporten_cache',
        backend='sqlite',
        expire_after=900,
        allowable_codes=(200,),
        include_get_headers=True,
    )


class DataportenGroupsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        return self.get_response(request)

    def process_view(self, request: HttpRequest, *args, **kwargs):
        if DataportenUser.valid_request(request):
            request.user.__class__ = DataportenUser
