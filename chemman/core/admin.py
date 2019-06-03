# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import *


admin.site.unregister(User)


class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name = _('Employee')
    verbose_name_plural = _('Employee')


class DepartmentInline(admin.StackedInline):
    model = Department.users.through
    verbose_name = _('Department')
    verbose_name_plural = _('Departments')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [EmployeeInline, DepartmentInline]
    list_display = ('username', 'get_departments', 'email', 'last_name',
                    'first_name', 'is_active', 'is_staff', 'last_login')
    list_display_links = ('username',)
    list_editable = ('is_active',)
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'departments')
    list_select_related = True
    search_fields = ('username', 'email', 'last_name', 'first_name')

    def get_departments(self, obj):
        return ', '.join([x.name for x in obj.departments.all()])

    get_departments.short_description = _('Departments')


class IdentifiersInline(admin.StackedInline):
    model = Identifiers


class PhysicalDataInline(admin.StackedInline):
    model = PhysicalData


class SynonymInline(admin.StackedInline):
    model = Synonym
    extra = 3


class ContactPersonInline(admin.StackedInline):
    model = ContactPerson
    extra = 2


@admin.register(Chemical)
class ChemicalAdmin(admin.ModelAdmin):
    date_hierarchy = 'last_updated'
    inlines = [SynonymInline, IdentifiersInline, PhysicalDataInline]
    list_display = ('get_name', 'get_cas', 'get_ghs_pics', 'special_log',
                    'cmr', 'formula', 'molar_mass', 'active')
    list_display_links = ('get_name',)
    list_editable = ('active',)
    list_filter = ('active', 'special_log', 'flammable', 'last_updated',
                   'added', 'cmr')
    list_select_related = True
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'name_en', 'iupac_name', 'iupac_name_en')

    def get_name(self, obj):
        return obj.display_name

    get_name.admin_order_field = 'name'
    get_name.short_description = _('Name')

    def get_cas(self, obj):
        if obj.identifiers:
            return obj.identifiers.cas or '-'
        return '-'

    get_cas.short_description = _('CAS')

    def get_structure(self, obj):
        if obj.structure:
            return mark_safe('<img src="{}" alt="{}" width="30">'.format(
                obj.structure.url, obj.display_name))
        return ''

    get_structure.short_description = _('Structure')

    def get_ghs_pics(self, obj):
        pics = []
        for pic in obj.pictograms.all():
            pics.append(
                '<img src="{url}" alt="{name}" width="30" '
                'title="{name}">'.format(
                    url=pic.image.url, name=pic)
            )
        if pics:
            return mark_safe('\n'.join(pics))
        return '-'

    get_ghs_pics.short_description = _('GHS Info')

    def save_model(self, req, obj, form, change):
        if not change:
            obj.added_by = req.user
        if not obj.wiki_link:
            obj.update_wiki_link()
        obj.save()


@admin.register(GHSPictogram)
class GHSPictogramAdmin(admin.ModelAdmin):
    list_display = ('get_image', '__str__')
    list_display_links = ('get_image', '__str__')
    search_fields = ('name',)

    def get_image(self, obj):
        return mark_safe('<img src="{}" alt="" width="30">'.format(
            obj.image.url, str(obj)))

    get_image.short_description = _('Pictogram')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    inlines = [ContactPersonInline]
    list_display = ('name', 'get_logo', 'short_name', 'phone',
                    'customer_number')
    list_display_links = ('name', 'get_logo')
    list_editable = ('short_name', 'phone', 'customer_number')
    search_fields = ('name', 'short_name', 'city')
    fieldsets = (
        (None, {
            'fields': ('name', 'short_name', 'customer_number'),
         }),
        (_('Contact Data'), {
            'fields': ('phone', 'fax', 'email'),
         }),
        (_('Address'), {
            'fields': ('street', 'zip_code', 'city', 'country'),
         }),
        (_('Additional'), {
            'fields': ('url', 'logo'),
            'classes': ('collapse',),
         }),
    )

    def get_logo(self, obj):
        if obj.logo:
            return mark_safe('<img src="{}" alt="{} Logo" width="25">'.format(
                obj.logo.url, obj.name))

    get_logo.short_description = _('Logo')


@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'company', 'responsible_for', 'direct_dialing')
    list_display_links = ('fullname',)
    list_filter = ('company__name',)
    list_select_related = True
    search_fields = ('last_name', 'company__name')

    def fullname(self, obj):
        if obj.first_name:
            return '{}, {}'.format(obj.last_name, obj.first_name)
        return obj.last_name

    fullname.short_description = _('Name')


@admin.register(Paragraph)
class ParagraphAdmin(admin.ModelAdmin):
    date_hierarchy = 'last_modified'
    list_display = ('__str__', 'number', 'added', 'author',
                    'last_modified', 'last_modified_by')
    list_display_links = ('__str__',)
    list_editable = ('number',)
    list_filter = ('added', 'last_modified')
    list_select_related = True
    search_fields = ('title', 'text')

    def save_model(self, req, obj, form, change):
        if not change:
            obj.author = req.user
        else:
            obj.last_modified_by = req.user
        obj.save()


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'street', 'city')
    list_display_links = ('name',)
    list_filter = ('city',)
    search_fields = ('name', 'identifier')


@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'department', 'type', 'consumption',
                    'observe', 'lockable')
    list_display_links = ('name',)
    list_editable = ('type', 'consumption', 'observe', 'lockable')
    list_filter = ('type', 'observe', 'lockable')
    list_select_related = True
    search_fields = ('name',)


@admin.register(StoragePlace)
class StoragePlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'storage', 'room', 'lockable')
    list_display_links = ('name',)
    list_editable = ('room', 'lockable')
    list_filter = ('storage', 'lockable')
    list_select_related = True
    search_fields = ('name', 'description')


@admin.register(StoredPackage)
class StoredPackageAdmin(admin.ModelAdmin):
    list_display = ('stored_chemical', 'place', 'package_id', 'content',
                    'unit', 'stored_by', 'container_material', 'empty')
    list_display_links = ('stored_chemical',)
    list_filter = ('place', 'stored_by', 'container_material', 'empty')
    list_select_related = True
    search_fields = ('stored_chemical__chemical__name', 'place__name')

    def save_model(self, req, obj, form, change):
        obj.stored_by = req.user
        obj.save()


@admin.register(PackageUsage)
class PackageUsageAdmin(admin.ModelAdmin):
    list_display = ('package', 'removed_quantity', 'removed_quantity_unit',
                    'usage_date', 'user', 'group', 'is_inventory')
    list_display_links = ('package',)
    list_filter = ('usage_date', 'user', 'group', 'is_inventory')
    list_select_related = True
    search_fields = ('user__username', 'group__name')


@admin.register(ChapterComment)
class ChapterCommentAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'get_title', 'author', 'added')
    list_display_links = ('chapter',)
    list_filter = ('chapter', 'author', 'added')
    list_select_related = True
    search_fields = ('title', 'chapter__title', 'author__username')

    def get_title(self, obj):
        if obj.title:
            return obj.title
        return _('[No title]')
    get_title.short_description = _('Title')

    def save_model(self, req, obj, form, change):
        if not change:
            obj.author = req.user
        obj.save()


@admin.register(StockLimit)
class StockLimitAdmin(admin.ModelAdmin):
    list_display = ('storage', 'chemical', 'type', 'stock', 'unit')
    list_display_links = ('storage', 'chemical')
    list_editable = ('stock', 'unit')
    list_filter = ('storage', 'type')
    list_select_related = True
    search_fields = ('storage__name', 'chemical__name')


@admin.register(LegalLimit)
class LegalLimitAdmin(admin.ModelAdmin):
    list_display = ('ident', 'text', 'type', 'threshold', 'stock', 'unit')
    list_display_links = ('ident',)
    list_editable = ('threshold',)
    list_filter = ('type',)
    list_select_related = True
    filter_horizontal = ('chemicals',)
    search_fields = ('ident', 'text', 'reference')


@admin.register(InventoryDifference)
class InventoryDifferenceAdmin(admin.ModelAdmin):
    list_display = ('get_package_id', 'get_name', 'saved', 'value', 'unit',
                    'user', 'note')
    list_display_links = ('get_package_id',)
    list_filter = ('saved',)
    list_select_related = True
    search_fields = ('package__stored_chemical__chemical__name',)

    def get_package_id(self, obj):
        return obj.package.package_id
    get_package_id.short_description = _('Package ID')

    def get_name(self, obj):
        return obj.package.stored_chemical.chemical.display_name
    get_name.short_description = _('Name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'count', 'user', 'delivered_count',
                    'stored', 'complete')
    list_display_links = ('barcode',)
    list_filter = ('user', 'stored', 'complete')
    list_select_related = True
    search_fields = ('barcode__chemical__name',)


@admin.register(OperatingInstruction)
class OperatingInstructionAdmin(admin.ModelAdmin):
    list_display = ('department', 'chemical', 'added', 'last_updated',
                    'last_updated_by')
    list_display_links = ('department',)
    list_filter = ('last_updated', 'department', 'last_updated_by')
    list_select_related = True
    search_fields = ('chemical__name', 'department__name')


admin.site.register(Bookmark)
admin.site.register(Group)
admin.site.register(Identifiers)
admin.site.register(PhysicalData)
admin.site.register(Synonym)
admin.site.register(DisposalInstructions)
admin.site.register(MaterialSafetyDataSheet)
admin.site.register(JournalType)
admin.site.register(JournalEntry)
admin.site.register(HazardStatement)
admin.site.register(EUHazardStatement)
admin.site.register(PrecautionaryStatement)
admin.site.register(StorageClass)
admin.site.register(StorageRestriction)
admin.site.register(Handbook)
admin.site.register(Chapter)
admin.site.register(HandbookImage)
admin.site.register(Department)
admin.site.register(Room)
admin.site.register(StoredChemical)
admin.site.register(Barcode)
admin.site.register(Consume)
admin.site.register(Notification)
