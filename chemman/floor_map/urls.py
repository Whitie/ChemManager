# -*- coding: utf-8 -*-

from django.conf.urls import url

from . import views


app_name = 'floor_map'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^edit/(?P<floor_id>\d+)/$', views.edit_map, name='edit-map'),
    url(r'^save/$', views.save_coords, name='save-coords'),
]
