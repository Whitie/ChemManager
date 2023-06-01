# -*- coding: utf-8 -*-

from django.urls import path

from . import views


app_name = 'operating_instruction_creator'

urlpatterns = [
    path('', views.index, name='index'),
    path('new/<int:chem_id>/', views.new_operating_instruction, name='new'),
    path('edit/<int:id>/', views.edit_operating_instruction, name='edit'),
    path('preview/<int:chem_id>/', views.preview, name='preview'),
    path('release/<int:id>/', views.release, name='release'),
    # API
    path('api/select-chemical/', views.select_chemical,
         name='api-select-chemical'),
    path('api/related-text/<int:chem_id>/', views.get_related_text,
         name='api-related-text'),
    path('api/text-for-import/', views.text_for_import, name='api-import'),
]
