from django.conf.urls import include, url
from django.contrib import admin
from semesterpage import views

urlpatterns = [
    url(r'^$', views.homepage, name='semesterpage-homepage'),
    url(r'^komfyr/login/$', views.homepage),
    url(r'^www/$', views.homepage),
    url(r'^komfyr/', include(admin.site.urls)),
    url(r'^accounts/profile/', views.profile, name='semesterpage-profile'),
    url(r'^kalender/(?P<calendar_name>[-\w]+)/$', views.calendar, name='semesterpage-calendar'),
    url(r'^(?P<study_program>[-\w]+)/(?P<semester_number>[1-9]|10|11|12)/$', views.simple_semester, name='semesterpage-simplesemester'),
    url(r'^(?P<study_program>[-\w]+)/(?P<main_profile>[-\w]+)/(?P<semester_number>[1-9]|10|11|12)/$', views.semester, name='semesterpage-semester'),
    url(r'^(?P<study_program>[-\w]+)/(?P<main_profile>[-\w]+)/$', views.main_profile_view, name='semesterpage-mainprofile'),
    url(r'^(?P<study_program>[-\w]+)/$', views.study_program_view, name='semesterpage-studyprogram'),
    url(r'^(?P<study_program>[-\w]+)/semester/(?P<semester_number>[1-9]|10)/request$', views.user_request, name='semesterpage-request'),
    url(r'^(?P<study_program>[-\w]+)/(?P<semester_number>[1-9]|10|11|12).Semester/(?P<main_profile>[-\w]+)/$', views.split_archive, name='semesterpage-splitarchive'),
    url(r'^(?P<study_program>[-\w]+)/(?P<semester_number>[1-9]|10|11|12).Semester/$', views.simple_archive, name='semesterpage-simplearchive'),
]
