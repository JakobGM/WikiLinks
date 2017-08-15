from django.conf.urls import include, url
from django.contrib import admin

from semesterpage import views

urlpatterns = [
    url(r'^$', views.homepage, name='semesterpage-homepage'),
    url(r'^www/$', views.homepage),

    # Admin page for contributors
    url(r'^oppdater/', include(admin.site.urls)),

    # For autocompletion of Courses in admin, with django-autocomplete-light
    url(r'^course-autocomplete/$', views.CourseAutocomplete.as_view(), name='semesterpage-course-autocomplete'),

    url(r'^accounts/profile/', views.profile, name='semesterpage-profile'),
    url(r'^kalender/(?P<calendar_name>[-\w]+)/$', views.calendar, name='semesterpage-calendar'),

    # View for updating a course homepage url from user input
    url(r'^ny_faghjemmeside/(?P<course_pk>\d+)/$', views.new_course_url, name='semesterpage-new_homepage_url'),

    url(r'^(?P<study_program>[-\w]+)/(?P<semester_number>[1-9]|10|11|12)/$', views.simple_semester, name='semesterpage-simplesemester'),
    url(r'^(?P<study_program>[-\w]+)/(?P<main_profile>[-\w]+)/(?P<semester_number>[1-9]|10|11|12)/$', views.semester, name='semesterpage-semester'),
    url(r'^(?P<study_program>[-\w]+)/(?P<main_profile>[-\w]+)/$', views.main_profile_view, name='semesterpage-mainprofile'),
    url(r'^(?P<study_program>[-\w]+)/$', views.study_program_view, name='semesterpage-studyprogram'),
    url(r'^(?P<study_program>[-\w]+)/(?P<semester_number>[1-9]|10|11|12).Semester/(?P<main_profile>[-\w]+)/$', views.split_archive, name='semesterpage-splitarchive'),
    url(r'^(?P<study_program>[-\w]+)/(?P<semester_number>[1-9]|10|11|12).Semester/$', views.simple_archive, name='semesterpage-simplearchive'),
]
