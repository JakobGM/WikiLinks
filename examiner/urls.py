from django.conf.urls import url

from examiner import views


urlpatterns = [
    url(
        r'^$',
        views.exams,
        name='all_exams',
    ),
    url(
        r'^verify$',
        views.VerifyView.as_view(),
        name='verify_random',
    ),
    url(
        r'^(?P<course_code>[a-zA-Z]{3,4}\d\d\d\d)$',
        views.exams,
        name='course',
    ),
]
