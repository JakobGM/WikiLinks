import logging

import requests
import requests_cache
from django.conf import settings

from .api import usergroups

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

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(request, 'user') and request.user.is_authenticated():
            try:
                pass
                # TODO: Add proxy model to user which includes the usergroups
            except SocialToken.DoesNotExist:
                # The user has not logged in with dataporten oAuth provider
                return
