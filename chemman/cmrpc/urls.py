# -*- coding: utf-8 -*-

from django.urls import path

from .views import ChemicalView, DeliveryView, LabelPrinterView

app_name = 'cmrpc'

urlpatterns = [
    path('chemicals/', ChemicalView.as_view()),
    path('delivery/', DeliveryView.as_view()),
    path('labels/', LabelPrinterView.as_view()),
]
