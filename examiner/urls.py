from django.conf.urls import include, url

from examiner import views


urlpatterns= [
    url(r'^', views.test, name='home'),
]
