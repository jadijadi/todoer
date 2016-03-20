from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^accounts/login/$', views.login_page, name='login_page'),
    url(r'^accounts/logout/$', views.logout_page, name='logout_page'),
    url(r'^task/([0-9]+)/done/$', views.taskdone, name='taskdone'),
    url(r'^task/([0-9]+)/redo/$', views.taskredo, name='taskredo'),
    url(r'^task/add/$', views.taskadd, name='taskadd'),
]
