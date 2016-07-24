from django.conf.urls import url
from semesterpage import views

urlpatterns = [
    url(r'^$', views.homepage, name='semesterpage-homepage'),
    url(r'^(?P<study_program>[-\w]+)/(?P<main_profile>[-\w]+)/(?P<semester_number>[1-9]|10)/$', views.semester, name='semesterpage-semester'),
    url(r'^(?P<study_program>[-\w]+)/$', views.study_program_view, name='semesterpage-studyprogram'),
    url(r'^(?P<study_program>[-\w]+)/semester/(?P<semester_number>[1-9]|10)/request$', views.user_request, name='semesterpage-request'),
]
