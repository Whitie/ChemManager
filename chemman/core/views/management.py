# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission, User
from django.db.models import Q
from django.shortcuts import redirect
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from ..manage_forms import (
    BuildingForm, DepartmentForm, NotificationForm, StorageForm,
    StoragePlaceForm, RoomForm
)
from ..models.base import Department, Notification
from ..models.storage import Building, Room, Storage, StoragePlace
from ..system_info import Hardware, Software
from ..utils import render, render_json


CUSTOM_PERMISSIONS = (
    'core.can_store', 'core.can_consume', 'core.can_transfer',
    'core.can_dispose', 'core.set_limits', 'core.manage_storage',
    'core.inventory', 'core.can_review', 'core.can_order', 'core.manage',
    'core.can_write_handbook', 'core.can_moderate_comments',
)


def get_permission_object(perm):
    app_label, codename = perm.split('.', 1)
    return Permission.objects.filter(
        content_type__app_label=app_label, codename=codename
    ).first()


def get_users_with_permission(perm, include_superuser=True):
    if isinstance(perm, six.string_types):
        pobj = get_permission_object(perm)
    else:
        pobj = perm
    query = Q(groups__permissions=pobj) | Q(user_permissions=pobj)
    if include_superuser:
        query |= Q(is_superuser=True)
    return User.objects.filter(query).distinct()


@login_required
def index(req):
    ctx = dict(title=_('Management'))
    return render(req, 'core/manage/index.html', ctx)


@login_required
def rights(req):
    show_all = req.GET.get('show_all', 'n') == 'y'
    custom_perms = {}
    if show_all:
        for perm in Permission.objects.all():
            custom_perms[perm.codename] = dict(
                name=perm.name, users=get_users_with_permission(perm)
            )
    else:
        for perm_name in CUSTOM_PERMISSIONS:
            perm = get_permission_object(perm_name)
            if perm is not None:
                custom_perms[perm.codename] = dict(
                    name=perm.name, users=get_users_with_permission(perm)
                )
    ctx = dict(title=_('Permissions'), custom_perms=custom_perms,
               show_all=show_all)
    return render(req, 'core/manage/rights.html', ctx)


@permission_required('core.manage_storage')
def buildings(req, building_id=None):
    buildings = Building.objects.all().order_by('name')
    if req.method == 'POST':
        if building_id is not None:
            building = Building.objects.get(pk=int(building_id))
            form = BuildingForm(req.POST, instance=building)
        else:
            form = BuildingForm(req.POST)
        try:
            form.save()
            messages.success(req, _('Building saved'))
        except Exception as err:
            messages.error(req, _('Error while saving: {}').format(err))
        return redirect('core:manage-buildings')
    if building_id is not None:
        building = Building.objects.get(pk=int(building_id))
        form = BuildingForm(instance=building)
        edit = True
    else:
        form = BuildingForm()
        edit = False
    ctx = dict(title=_('Buildings'), buildings=buildings, form=form,
               edit=edit, reset_url='core:manage-buildings')
    return render(req, 'core/manage/buildings.html', ctx)


@permission_required('core.manage_storage')
def departments(req, dep_id=None):
    deps = Department.objects.all().order_by('name')
    if req.method == 'POST':
        if dep_id is not None:
            dep = Department.objects.get(pk=int(dep_id))
            form = DepartmentForm(req.POST, instance=dep)
        else:
            form = DepartmentForm(req.POST)
        try:
            form.save()
            messages.success(req, _('Department saved'))
        except Exception as err:
            messages.error(req, _('Error while saving: {}').format(err))
        return redirect('core:manage-departments')
    if dep_id is not None:
        dep = Department.objects.get(pk=int(dep_id))
        form = DepartmentForm(instance=dep)
        edit = True
    else:
        form = DepartmentForm()
        edit = False
    ctx = dict(title=_('Departments'), deps=deps, form=form, edit=edit,
               reset_url='core:manage-departments')
    return render(req, 'core/manage/departments.html', ctx)


@permission_required('core.manage_storage')
def storages(req, storage_id=None):
    buildings = Building.objects.all()
    if req.method == 'POST':
        if storage_id is not None:
            storage = Storage.objects.get(pk=int(storage_id))
            form = StorageForm(req.POST, instance=storage)
        else:
            form = StorageForm(req.POST)
        try:
            form.save()
            messages.success(req, _('Storage saved'))
        except Exception as err:
            messages.error(req, _('Error while saving: {}').format(err))
        return redirect('core:manage-storages')
    if storage_id is not None:
        storage = Storage.objects.get(pk=int(storage_id))
        form = StorageForm(instance=storage)
        edit = True
    else:
        form = StorageForm()
        edit = False
    ctx = dict(title=_('Storages'), buildings=buildings, form=form, edit=edit,
               reset_url='core:manage-storages')
    return render(req, 'core/manage/storages.html', ctx)


@permission_required('core.manage_storage')
def places(req, place_id=None):
    storages = Storage.objects.filter(
        places__isnull=False
    ).distinct().order_by('name')
    if req.method == 'POST':
        if place_id is not None:
            place = StoragePlace.objects.get(pk=int(place_id))
            form = StoragePlaceForm(req.POST, instance=place)
        else:
            form = StoragePlaceForm(req.POST)
        try:
            form.save()
            messages.success(req, _('Place saved'))
        except Exception as err:
            messages.error(req, _('Error while saving: {}').format(err))
        return redirect('core:manage-places')
    if place_id is not None:
        place = StoragePlace.objects.get(pk=int(place_id))
        form = StoragePlaceForm(instance=place)
        edit = True
    else:
        form = StoragePlaceForm()
        edit = False
    ctx = dict(title=_('Places'), storages=storages, form=form, edit=edit,
               reset_url='core:manage-places')
    return render(req, 'core/manage/places.html', ctx)


@permission_required('core.manage_storage')
def rooms(req, room_id=None):
    buildings = Building.objects.all()
    if req.method == 'POST':
        if room_id is not None:
            room = Room.objects.get(pk=int(room_id))
            form = RoomForm(req.POST, instance=room)
        else:
            form = RoomForm(req.POST)
        try:
            form.save()
            messages.success(req, _('Room saved'))
        except Exception as err:
            messages.error(req, _('Error while saving: {}').format(err))
        return redirect('core:manage-rooms')
    if room_id is not None:
        room = Room.objects.get(pk=int(room_id))
        form = RoomForm(instance=room)
        edit = True
    else:
        form = RoomForm()
        edit = False
    ctx = dict(title=_('Rooms'), buildings=buildings, form=form, edit=edit,
               reset_url='core:manage-rooms')
    return render(req, 'core/manage/rooms.html', ctx)


@permission_required('core.manage_storage')
def legal_limits(req):
    return HttpResponse('Legal Limits')


@permission_required('core.manage')
def notices(req):
    notices = Notification.objects.all().order_by('-added')
    if req.method == 'POST':
        form = NotificationForm(req.POST)
        note = form.save(commit=False)
        note.added_by = req.user
        try:
            note.save()
            messages.success(req, _('Notification was saved'))
        except Exception as err:
            messages.error(req, _('Error while saving: {}').format(err))
        return redirect('core:manage-notices')
    form = NotificationForm()
    ctx = dict(title=_('Notifications'), notices=notices, form=form,
               reset_url='core:manage-notices')
    return render(req, 'core/manage/notifications.html', ctx)


@permission_required('core.change_chemical')
def edit_chemical(req):
    return HttpResponse('Edit Chemical')


def about(req):
    ctx = dict(title=_('System Info'), hardware=Hardware(),
               software=Software())
    return render(req, 'core/about.html', ctx)
