# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Floor, FloorStorage

# Register your models here.


@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('building', 'level', 'name')
    list_display_links = ('building',)
    list_editable = ('level', 'name')
    list_filter = ('building__name',)
    list_select_related = True
    search_fields = ('building__name', 'name')


@admin.register(FloorStorage)
class FloorStorageAdmin(admin.ModelAdmin):
    list_display = ('floor', 'storage', 'x', 'y', 'is_lockable')
    list_display_links = ('floor',)
    list_editable = ('x', 'y')
    list_filter = ('floor',)
    list_select_related = True
    search_fields = ('floor_name', 'floor__building__name', 'storage__name')

    def is_lockable(self, obj):
        return obj.storage.lockable
    is_lockable.boolean = True
    is_lockable.short_description = _('Lockable')
