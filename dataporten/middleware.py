import logging

from django.conf import settings

import requests
import requests_cache

# Cache requests for 15 minutes
if settings.DATAPORTEN_CACHE_REQUESTS:
    requests_cache.install_cache(
        settings.DATAPORTEN_CACHE_PATH + 'dataporten_cache',
        backend='sqlite',
        expire_after=900,
        allowable_codes=(200,),
        include_get_headers=True,
    )

logger = logging.getLogger(__name__)


class GetDataportenGroups(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Ignore if request is not made to API
        if not request.path.startswith('/v1'):
            return

        token = request.META.get('HTTP_X_DATAPORTEN_TOKEN', None)
        if not token:
            if not request.user.is_superuser:
                logger.info(
                    'Request received to {} without '
                    'x-dataporten-token in header'.format(request.path)
                )
            request.groups = []
            request.dataporten_admin = False
            return

        url = settings.DATAPORTEN_GROUP_API_URL
        request.dataporten_token = token
        headers = {
            'Authorization': 'Bearer {}'.format(request.dataporten_token)
        }

        try:
            # Add groups to request
            res = requests.get(url, headers=headers)
            groups = res.json()
            request.groups = groups

            logger.info(
                'Dataporten response code: {}, token {}, request-id: {}, '
                'from cache: {}, group length: {}'
                .format(
                    res.status_code,
                    token,
                    res.headers.get('X-Request-Id'),
                    getattr(res, 'from_cache', False),
                    len(groups)
                ))

            # If not groups returned, and request is not cached,
            # we assume something has gone wrong in dataporten
            if len(groups) <= 0 and not getattr(res, 'from_cache', False):
                logger.error(
                    'Dataporten group API returned groups of length 0: '
                    'token {}, request-id: {} '
                    .format(token, res.headers.get('X-Request-Id')))

            # Add dataporten_admin=True to request if part of admin group
            admin_id = settings.DATAPORTEN_ADMIN_GROUP_ID
            is_admin = any(g.get('id', None) == admin_id for g in groups)
            request.dataporten_admin = is_admin
        except requests.RequestException as e:
            request.groups = []
            request.dataporten_admin = False
            logger.error((
                'Dataporten: Error when requesting groups: {}. Response: {}'
                .format(e, getattr(e.response, 'text', ''))
            ))
        except (KeyError, AttributeError) as e:
            request.groups = getattr(request, 'groups', [])
            request.dataporten_admin = getattr(
                request, 'dataporten_admin', False)
            logger.info((
                'Dataporten: Error encountered when parsing groups: {}. '
                'Response: {}. '
                'Token: {}. '
                .format(e, res.text, token)
            ))
