# -*- coding: utf-8 -*-

from django.urls import path

from . import views


app_name = 'operating_instruction_creator'

urlpatterns = [
    path('', views.index, name='index'),
    path('edit/<int:id>/', views.edit_operating_instruction, name='edit'),
]
