# -*- coding: utf-8 -*-

from django.urls import path

from . import views


app_name = 'msds_collector'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('list/', views.list_uploads, name='list'),
    path('detail/<int:upload_id>/', views.detail, name='detail'),
    path('parsing_finished/<int:upload_id>/', views.parsing_finished,
         name='parsing-finished'),
    path('save/', views.save_basics, name='save'),
    path('transfer/<int:uid>/', views.transfer, name='transfer'),
    path('add-to-db/<int:pid>/', views.add_to_db, name='add'),
    path('compare/<int:pid>/<int:chem_id>/', views.compare,
         name='compare'),
    path('delete/', views.delete_upload, name='delete'),
]
