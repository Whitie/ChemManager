from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views
from django.urls import include, path
from django.views.generic import RedirectView

from django_spaghetti.views import Plate
from rest_framework import routers

from core.utils import is_active
from core.views import api


router = routers.DefaultRouter()
router.register('storages', api.StorageViewSet)
router.register('places', api.StoragePlaceViewSet)
router.register('packages', api.StoredPackageViewSet)


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
    # REST Framework
    path('api/', include(router.urls)),
    path(
        'api-auth/',
        include('rest_framework.urls', namespace='rest_framework')
    ),
    # Deprecated
    path('rpc/', include('cmrpc.urls')),
]

if settings.DEBUG or settings.SERVE_LAN:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()

if is_active('floor_map'):
    urlpatterns += [
        path('floor-map/', include('floor_map.urls', namespace='fm')),
    ]

if is_active('msds_collector'):
    urlpatterns += [
        path('msds_collector/', include('msds_collector.urls',
                                        namespace='msds'))
    ]

if is_active('operating_instruction_creator'):
    urlpatterns += [
        path('oic/', include('operating_instruction_creator.urls',
                             namespace='oic'))
    ]
