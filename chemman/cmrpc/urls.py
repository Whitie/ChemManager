# -*- coding: utf-8 -*-

from django.conf.urls import url

from .views import ChemicalView, DeliveryView, LabelPrinterView


urlpatterns = [
    url(r'^chemicals/$', ChemicalView.as_view()),
    url(r'^delivery/$', DeliveryView.as_view()),
    url(r'^labels/$', LabelPrinterView.as_view()),
]
