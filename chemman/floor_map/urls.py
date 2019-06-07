# -*- coding: utf-8 -*-

from django.urls import path

from . import views


app_name = 'floor_map'

urlpatterns = [
    path('', views.index, name='index'),
    path('edit/<int:floor_id>/', views.edit_map, name='edit-map'),
    path('save/', views.save_coords, name='save-coords'),
]
