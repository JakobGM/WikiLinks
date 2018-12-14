from django.conf.urls import url

from examiner import views


urlpatterns = [
    url(
        r'^$',
        views.exams,
        name='all_exams',
    ),
    url(
        r'^(?P<course_code>[a-zA-Z]{3,4}\d\d\d\d)$',
        views.exams,
        name='course',
    ),
    url(
        r'^backup/(?P<course_code>[a-zA-Z]{3,4}\d\d\d\d)$',
        views.backup,
        name='backup',
    ),
    url(
        r'^crawl/$',
        views.crawl,
        name='crawl',
    ),
    url(
        r'^parse/$',
        views.parse,
        name='parse',
    ),
]