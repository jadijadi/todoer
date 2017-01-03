from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^accounts/login/$', views.login_page, name='login_page'),
    url(r'^accounts/logout/$', views.logout_page, name='logout_page'),
    url(r'^accounts/register/$', views.register, name='register'),
    url(r'^accounts/resetpassword/$', views.resetpassword, name='resetpassword'),

    url(r'^task/([0-9]+)/done/$', views.taskdone, name='taskdone'),
    url(r'^task/edit/$', views.taskedit, name='taskedit'),
    url(r'^task/([0-9]+)/redo/$', views.taskredo, name='taskredo'),
    url(r'^task/([0-9]+)/delete/$', views.deletetask, name='deletetask'),
    url(r'^task/add/$', views.taskadd, name='taskadd'),
]
