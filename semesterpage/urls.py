from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^$', views.homepage, name='semesterpage-homepage'),
    url(r'^semester/(?P<semester_number>[1-9]|10)/$', views.semester, name='semesterpage-semester'),
    url(r'^semester/(?P<semester_number>[1-9]|10)/request$', views.user_request, name='semesterpage-request'),
]
