from django.conf.urls import url

from examiner import views


urlpatterns = [
    url(
        r'^$',
        views.SearchView.as_view(),
        name='search',
    ),
    url(
        r'^all$',
        views.ExamsView.as_view(),
        name='all_exams',
    ),
    url(
        r'^verify$',
        views.VerifyView.as_view(),
        name='verify_random',
    ),
    url(
        r'^verify/(?P<sha1_hash>[0-9a-f]{40})$',
        views.VerifyView.as_view(),
        name='verify_pdf',
    ),
    url(
        r'^course/(?P<course_code>.+)$',
        views.ExamsView.as_view(),
        name='course',
    ),
    url(
        r'^course-autocomplete/$',
        views.CourseWithExamsAutocomplete.as_view(),
        name='course_autocomplete',
    ),
]
