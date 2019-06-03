# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^list/$', views.list_uploads, name='list'),
    url(r'^detail/(?P<upload_id>\d+)/$', views.detail, name='detail'),
    url(r'^parsing_finished/(?P<upload_id>\d+)/$', views.parsing_finished,
        name='parsing-finished'),
    url(r'^save/$', views.save_basics, name='save'),
    url(r'^transfer/(?P<uid>\d+)/$', views.transfer, name='transfer'),
    url(r'^add-to-db/(?P<pid>\d+)/$', views.add_to_db, name='add'),
    url(r'^compare/(?P<pid>\d+)/(?P<chem_id>\d+)/$', views.compare,
        name='compare'),
    url(r'^delete/$', views.delete_upload, name='delete'),
]
