from django.conf.urls import url

from examiner import views


urlpatterns = [
    url(
        r'^$',
        views.all_exams,
        name='all_exams',
    ),
    url(
        r'^(?P<course_code>[a-zA-Z]{3,4}\d\d\d\d)$',
        views.course,
        name='course',
    ),
    url(
        r'^crawl/$',
        views.crawl,
        name='crawl',
    ),
]
