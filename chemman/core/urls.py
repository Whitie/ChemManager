# -*- coding: utf-8 -*-

from django.urls import path, re_path
from django.views.i18n import JavaScriptCatalog

from . import views
from .views import handbook, management, orders, pdf


app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('info/', views.info, name='info'),
    path('info/whc/', views.info_whc, name='info-whc'),
    path('info/hp-statements/', views.info_hp, name='info-hp'),
    path('info/ghs/', views.info_ghs, name='info-ghs'),
    path('info/usage/', views.info_tox_usage, name='info-usage'),
    path('info/operating_instructions/', views.info_operating_instructions,
         name='info-opinst'),
    path('search/', views.search, name='search'),
    path('search/<searchstring>/', views.search, name='search'),
    path('search_extended/', views.extended_search, name='ext-search'),
    path('detail/by-id/<int:cid>/', views.detail_by_id,
         name='detail-by-id'),
    path('detail/by-slug/<slug:slug>/', views.detail_by_slug,
         name='detail-by-slug'),
    path('list/', views.choose_list, name='choose-list'),
    path('list/<name>/<param>/', views.list_chemicals,
         name='list-chemicals'),
]

# API
urlpatterns += [
    path('api/login/', views.api_login, name='api-login'),
    path('api/bookmark/add/', views.add_bookmark, name='api-add-bookmark'),
    path('api/bookmark/delete/', views.api_delete_bookmark,
         name='api-del-bookmark'),
    path('api/search/', views.api_search, name='api-search'),
    path('api/search/form/', views.api_get_search_form,
         name='api-search-form'),
    path('api/autocomplete/chemical/', views.api_autocomplete,
         name='api-autocomplete-chemical'),
    path('api/inventory/chemical/<int:chem_id>/',
         views.api_inventory_chemical, name='api-inventory-chemical'),
    path('api/inventory/package/<int:package_id>/',
         views.api_inventory_package, name='api-inventory-package'),
    path('api/inventory/save/', views.api_inventory_save,
         name='api-inventory-save'),
    path('api/limit/<int:stored_chem_id>/<int:storage_id>/',
         views.api_stock_limit, name='api-limit'),
    path('api/lists/', views.api_get_lists, name='api-get-lists'),
    path('api/storages/<int:chem_id>/', views.api_storages,
         name='api-storages'),
    path('api/consume/chemical/', views.api_consume_chem,
         name='api-consume-chem'),
    path('api/consume/storage/', views.api_storage_for_chemical,
         name='api-consume-storage'),
    path('api/consume/packages/', views.api_get_packages,
         name='api-consume-packages'),
    path('api/delivery/', orders.api_delivery, name='api-delivery'),
    path('api/delivery/store/fast/', orders.api_store_fast,
         name='api-delivery-store-fast'),
    path('api/delivery/store/extra/', orders.api_store_extra,
         name='api-delivery-store-extra'),
    path('api/chemicals/special_log/', views.api_get_special_log_list,
         name='api-special_log-list'),
    path('api/observe/storage/', views.api_check_observe,
         name='api-observe'),
    path('api/stocklimit/set/', views.save_stocklimit,
         name='api-set-stocklimit'),
    path('api/consume/wrong-brutto/', views.api_wrong_brutto,
         name='api-consume-wrong-brutto'),
]

# Images
urlpatterns += [
    re_path(r'^qr/info/(?P<image_format>(svg|png))/(?P<slug>.+)/$',
            views.chem_qrcode, name='qr-info'),
    re_path(r'^qr/package/(?P<image_format>(svg|png))/(?P<package_id>.+)/$',
            views.package_qrcode, name='qr-package'),
    path('qr/print/packages/', views.print_package_ids,
         name='qr-print-packages'),
    # Download package data as csv for labelprinter
    path('csv/packages/download/', views.download_labels_as_csv,
         name='download-packages-csv'),
]

# Storage
urlpatterns += [
    path('storage/package/<int:pid>/', views.package_info,
         name='package-info'),
    path('storage/package/by-uid/<package_id>/',
         views.package_info_by_uid, name='package-info-by-uid'),
    path('storage/packages/history/', views.packages_history,
         name='packages-history'),
    path('storage/package/new/<int:chem_id>/',
         views.store_new_package, name='package-new'),
    path('storage/package/new/<int:stored_chem_id>/<int:storage_id>/',
         views.store_new_package_2, name='package-new'),
    path('storage/package/dispose/<int:package_id>/', views.dispose,
         name='package-dispose'),
    path('storage/transfer/<int:package_id>/', views.transfer,
         name='package-transfer'),
    path('storage/inventory/chemical/<int:chem_id>/',
         views.chem_inventory, name='chem-inventory'),
    path('storage/inventory/<int:storage_id>/',
         views.storage_inventory, name='storage-inventory'),
    path('storage/inventory/make/<int:storage_id>/',
         views.make_inventory, name='storage-inventory-make'),
    path('storage/inventory/result/<int:storage_id>/',
         views.inventory_result, name='storage-inventory-result'),
    path('storage/', views.storage_index, name='storage-index'),
    path('storage/consume/', views.select_chemical_for_consume,
         name='consume-select'),
    path('storage/consume/<int:package_id>/', views.consume,
         name='consume'),
    path('storage/package/remove/', views.choose_removal,
         name='package-remove'),
    path('storage/packages/merge/<int:storage_id>/<int:chem_id>/',
         views.merge_packages, name='packages-merge'),
    path('storage/packages/merge/get/', views.get_merge_packages,
         name='packages-merge-get'),
    path('storage/packages/merge/do/', views.do_merge,
         name='packages-merge-do'),
    # PDF
    path('storage/pdf/inventory/<int:storage_id>/', pdf.make_inventory_list,
         name='storage-pdf-inventory'),
    # Info
    path('info/storage/classes/', views.storage_classes_info,
         name='storage-classes-info'),
    path('info/storage/chemicals/', views.info_stored_chemicals,
         name='info-stored-chemicals'),
    path('info/storage/observe/<int:storage_id>/', views.check_observe,
         name='info-observe'),
    path('storage/stocklimits/<int:storage_id>/', views.set_stocklimits,
         name='set-stocklimits'),
    # Delivery
    path('delivery/', orders.delivery, name='delivery'),
    path('delivery/store/packages/', orders.delivery_store_packages,
         name='delivery-store-packages'),
    path('delivery/initial/', orders.initial_delivery,
         name='delivery-initial'),
    path('delivery/initial/result/', orders.initial_delivery_result,
         name='delivery-initial-result'),
    path('delivery/initial/box/', orders.deliver_box,
         name='delivery-initial-box'),
    # Order
    path('order/old/<int:package_id>/', orders.new_order_old_package,
         name='order-old'),
    path('info/orders/', orders.info_orders, name='info-orders'),
    path('info/supplier/<int:sid>/', orders.chems_of_supplier,
         name='info-supplier'),
]

# Handbooks
urlpatterns += [
    path('handbook/', handbook.overview, name='hb-overview'),
    path('handbook/<int:hb_id>/', handbook.handbook, name='hb-handbook'),
    path('handbook/<int:hb_id>/<int:chapter>/', handbook.chapter,
         name='hb-chapter'),
    path('handbook/chapter/add/<int:hb_id>/', handbook.add_chapter,
         name='hb-add-chapter'),
    path('handbook/paragraph/add/<int:chapter>/', handbook.add_paragraph,
         name='hb-add-paragraph'),
    path('handbook/paragraph/edit/<int:paragraph>/',
         handbook.edit_paragraph, name='hb-edit-paragraph'),
]

# Handbook API
urlpatterns += [
    path('api/handbook/create/', handbook.add_handbook, name='hb-create'),
    path('api/handbook/delete/', handbook.delete_handbook,
         name='hb-delete'),
    path('api/handbook/chapter/delete/', handbook.delete_chapter,
         name='hb-delete-chapter'),
]

# Management
urlpatterns += [
    path('manage/', management.index, name='manage'),
    path('manage/buildings/', management.buildings,
         name='manage-buildings'),
    path('manage/buildings/<int:building_id>/', management.buildings,
         name='manage-buildings'),
    path('manage/departments/', management.departments,
         name='manage-departments'),
    path('manage/departments/<int:dep_id>/', management.departments,
         name='manage-departments'),
    path('manage/storages/', management.storages, name='manage-storages'),
    path('manage/storages/<int:storage_id>/', management.storages,
         name='manage-storages'),
    path('manage/places/', management.places, name='manage-places'),
    path('manage/places/<int:place_id>/', management.places,
         name='manage-places'),
    path('manage/rooms/', management.rooms, name='manage-rooms'),
    path('manage/rooms/<int:room_id>/', management.rooms,
         name='manage-rooms'),
    path('manage/limits/', management.legal_limits, name='manage-limits'),
    path('manage/notice/add/', management.notices, name='manage-notices'),
    path('manage/chemicals/edit/', management.edit_chemical,
         name='manage-chemicals-edit'),
    path('manage/rights/', management.rights, name='manage-rights'),

    path('about/', management.about, name='about'),
]

urlpatterns += [
    path('jsi18n/', JavaScriptCatalog.as_view(packages=['core']),
         name='javascript-catalog'),
]
