# -*- coding: utf-8 -*-
"""chemman URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.urls import include, path
from django.views.generic import RedirectView

from django_spaghetti.views import Plate

from core.utils import is_active


urlpatterns = [
    path('', RedirectView.as_view(pattern_name=settings.START_VIEW)),
    path('admin/', admin.site.urls),
    path('core/', include('core.urls', namespace='core')),
    path('accounts/login/', views.LoginView.as_view(),
         {'template_name': 'core/login.html'}),
    path(
        'model_graph/', Plate.as_view(
            plate_template_name='3rd_party/django_spaghetti/plate.html',
            meatball_template_name='3rd_party/django_spaghetti/meatball.html'
         )
    ),
    path('rpc/', include('cmrpc.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

if is_active('floor_map'):
    urlpatterns += [
        path('floor-map/', include('floor_map.urls', namespace='fm')),
    ]

if is_active('msds_collector'):
    urlpatterns += [
        path('msds_collector/', include('msds_collector.urls',
                                        namespace='msds'))
    ]
