# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.views.i18n import JavaScriptCatalog

from . import views
from .views import handbook, management, orders

app_name = 'core'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^profile/$', views.profile_view, name='profile'),
    url(r'^info/$', views.info, name='info'),
    url(r'^info/whc/$', views.info_whc, name='info-whc'),
    url(r'^info/hp-statements/$', views.info_hp, name='info-hp'),
    url(r'^info/ghs/$', views.info_ghs, name='info-ghs'),
    url(r'^info/usage/$', views.info_tox_usage, name='info-usage'),
    url(r'^info/operating_instructions/$', views.info_operating_instructions,
        name='info-opinst'),
    url(r'^search/$', views.search, name='search'),
    url(r'^search/(?P<searchstring>.+)/$', views.search, name='search'),
    url(r'^search_extended/$', views.extended_search, name='ext-search'),
    url(r'^detail/by-id/(?P<cid>\d+)/$', views.detail_by_id,
        name='detail-by-id'),
    url(r'^detail/by-slug/(?P<slug>.+)/$', views.detail_by_slug,
        name='detail-by-slug'),
    url(r'^list/$', views.choose_list, name='choose-list'),
    url(r'^list/(?P<name>.+)/(?P<param>.+)/$', views.list_chemicals,
        name='list-chemicals'),
]

# API
urlpatterns += [
    url(r'api/login/$', views.api_login, name='api-login'),
    url(r'^api/bookmark/add/$', views.add_bookmark, name='api-add-bookmark'),
    url(r'^api/bookmark/delete/$', views.api_delete_bookmark,
        name='api-del-bookmark'),
    url(r'^api/search/$', views.api_search, name='api-search'),
    url(r'^api/search/form/$', views.api_get_search_form,
        name='api-search-form'),
    url(r'^api/autocomplete/chemical/$', views.api_autocomplete,
        name='api-autocomplete-chemical'),
    url(r'^api/inventory/chemical/(?P<chem_id>\d+)/$',
        views.api_inventory_chemical, name='api-inventory-chemical'),
    url(r'^api/inventory/package/(?P<package_id>\d+)/$',
        views.api_inventory_package, name='api-inventory-package'),
    url(r'^api/inventory/save/$', views.api_inventory_save,
        name='api-inventory-save'),
    url(r'^api/limit/(?P<stored_chem_id>\d+)/(?P<storage_id>\d+)/$',
        views.api_stock_limit, name='api-limit'),
    url(r'^api/lists/$', views.api_get_lists, name='api-get-lists'),
    url(r'^api/storages/(?P<chem_id>\d+)/$', views.api_storages,
        name='api-storages'),
    url(r'^api/consume/chemical/$', views.api_consume_chem,
        name='api-consume-chem'),
    url(r'^api/consume/storage/$', views.api_storage_for_chemical,
        name='api-consume-storage'),
    url(r'^api/consume/packages/$', views.api_get_packages,
        name='api-consume-packages'),
    url(r'^api/delivery/$', orders.api_delivery, name='api-delivery'),
    url(r'^api/delivery/store/fast/$', orders.api_store_fast,
        name='api-delivery-store-fast'),
    url(r'^api/delivery/store/extra/$', orders.api_store_extra,
        name='api-delivery-store-extra'),
    url(r'^api/chemicals/special_log/$', views.api_get_special_log_list,
        name='api-special_log-list'),
    url(r'^api/observe/storage/$', views.api_check_observe,
        name='api-observe'),
    url(r'^api/stocklimit/set/$', views.save_stocklimit,
        name='api-set-stocklimit'),
    url(r'^api/consume/wrong-brutto/$', views.api_wrong_brutto,
        name='api-consume-wrong-brutto'),
]

# Images
urlpatterns += [
    url(r'^qr/info/(?P<image_format>(svg|png))/(?P<slug>.+)/$',
        views.chem_qrcode, name='qr-info'),
    url(r'^qr/package/(?P<image_format>(svg|png))/(?P<package_id>.+)/$',
        views.package_qrcode, name='qr-package'),
    url(r'^qr/print/packages/$', views.print_package_ids,
        name='qr-print-packages'),
]

# Storage
urlpatterns += [
    url(r'^storage/package/(?P<pid>\d+)/$', views.package_info,
        name='package-info'),
    url(r'^storage/package/by-uid/(?P<package_id>.+)/$',
        views.package_info_by_uid, name='package-info-by-uid'),
    url(r'^storage/packages/history/', views.packages_history,
        name='packages-history'),
    url(r'^storage/package/new/(?P<chem_id>\d+)/$',
        views.store_new_package, name='package-new'),
    url(r'^storage/package/new/(?P<stored_chem_id>\d+)/(?P<storage_id>\d+)/$',
        views.store_new_package_2, name='package-new'),
    url(r'^storage/package/dispose/(?P<package_id>\d+)/$', views.dispose,
        name='package-dispose'),
    url(r'^storage/transfer/(?P<package_id>\d+)/$', views.transfer,
        name='package-transfer'),
    url(r'^storage/inventory/chemical/(?P<chem_id>\d+)/$',
        views.chem_inventory, name='chem-inventory'),
    url(r'^storage/inventory/(?P<storage_id>\d+)/$',
        views.storage_inventory, name='storage-inventory'),
    url(r'^storage/inventory/make/(?P<storage_id>\d+)/$',
        views.make_inventory, name='storage-inventory-make'),
    url(r'^storage/inventory/result/(?P<storage_id>\d+)/$',
        views.inventory_result, name='storage-inventory-result'),
    url(r'^storage/$', views.storage_index, name='storage-index'),
    url(r'^storage/consume/$', views.select_chemical_for_consume,
        name='consume-select'),
    url(r'^storage/consume/(?P<package_id>\d+)/$', views.consume,
        name='consume'),
    url(r'^storage/package/remove/$', views.choose_removal,
        name='package-remove'),
    url(r'^storage/packages/merge/(?P<storage_id>\d+)/(?P<chem_id>\d+)/$',
        views.merge_packages, name='packages-merge'),
    url(r'storage/packages/merge/get/$', views.get_merge_packages,
        name='packages-merge-get'),
    url(r'storage/packages/merge/do/$', views.do_merge,
        name='packages-merge-do'),
    # Info
    url(r'^info/storage/classes/$', views.storage_classes_info,
        name='storage-classes-info'),
    url(r'^info/storage/chemicals/$', views.info_stored_chemicals,
        name='info-stored-chemicals'),
    url(r'^info/storage/observe/(?P<storage_id>\d+)/$', views.check_observe,
        name='info-observe'),
    url(r'^storage/stocklimits/(?P<storage_id>\d+)/$', views.set_stocklimits,
        name='set-stocklimits'),
    # Delivery
    url(r'^delivery/$', orders.delivery, name='delivery'),
    url(r'^delivery/store/packages/$', orders.delivery_store_packages,
        name='delivery-store-packages'),
    url(r'^delivery/initial/$', orders.initial_delivery,
        name='delivery-initial'),
    url(r'^delivery/initial/result/$', orders.initial_delivery_result,
        name='delivery-initial-result'),
    # Order
    url(r'^order/old/(?P<package_id>\d+)/$', orders.new_order_old_package,
        name='order-old'),
    url(r'^info/orders/$', orders.info_orders, name='info-orders'),
    url(r'^info/supplier/(?P<sid>\d+)/$', orders.chems_of_supplier,
        name='info-supplier'),
]

# Handbooks
urlpatterns += [
    url(r'^handbook/$', handbook.overview, name='hb-overview'),
    url(r'^handbook/(?P<hb_id>\d+)/$', handbook.handbook, name='hb-handbook'),
    url(r'^handbook/(?P<hb_id>\d+)/(?P<chapter>\d+)/$', handbook.chapter,
        name='hb-chapter'),
    url(r'^handbook/chapter/add/(?P<hb_id>\d+)/$', handbook.add_chapter,
        name='hb-add-chapter'),
    url(r'^handbook/paragraph/add/(?P<chapter>\d+)/$', handbook.add_paragraph,
        name='hb-add-paragraph'),
    url(r'^handbook/paragraph/edit/(?P<paragraph>\d+)/$',
        handbook.edit_paragraph, name='hb-edit-paragraph'),
]

# Handbook API
urlpatterns += [
    url(r'^api/handbook/create/$', handbook.add_handbook, name='hb-create'),
    url(r'^api/handbook/delete/$', handbook.delete_handbook,
        name='hb-delete'),
    url(r'^api/handbook/chapter/delete/$', handbook.delete_chapter,
        name='hb-delete-chapter'),
]

# Management
urlpatterns += [
    url(r'^manage/$', management.index, name='manage'),
    url(r'^manage/buildings/$', management.buildings,
        name='manage-buildings'),
    url(r'^manage/buildings/(?P<building_id>\d+)/$', management.buildings,
        name='manage-buildings'),
    url(r'^manage/departments/$', management.departments,
        name='manage-departments'),
    url(r'^manage/departments/(?P<dep_id>\d+)/$', management.departments,
        name='manage-departments'),
    url(r'^manage/storages/$', management.storages, name='manage-storages'),
    url(r'^manage/storages/(?P<storage_id>\d+)/$', management.storages,
        name='manage-storages'),
    url(r'^manage/places/$', management.places, name='manage-places'),
    url(r'^manage/places/(?P<place_id>\d+)/$', management.places,
        name='manage-places'),
    url(r'^manage/rooms/$', management.rooms, name='manage-rooms'),
    url(r'^manage/rooms/(?P<room_id>\d+)/$', management.rooms,
        name='manage-rooms'),
    url(r'^manage/limits/$', management.legal_limits, name='manage-limits'),
    url(r'^manage/notice/add/$', management.notices, name='manage-notices'),
    url(r'^manage/chemicals/edit/$', management.edit_chemical,
        name='manage-chemicals-edit'),
    url(r'^manage/rights/$', management.rights, name='manage-rights'),

    url(r'^about/$', management.about, name='about'),
]

urlpatterns += [
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(packages=['core']),
        name='javascript-catalog'),
]
