# -*- coding: utf-8 -*-

from datetime import date, timedelta

from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.forms import formset_factory
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from ..forms import (
    DeliverOrderForm, DeliverJSONForm, InitialDeliveryForm
)
from ..models import Company
from ..models.storage import (
    Storage, StoredPackage, StoragePlace, Order, Barcode,
    MASS_CHOICES, CONTAINER_MATERIAL_CHOICES, COMPOSITION_CHOICES
)
from ..utils import render, render_json, render_to_string
from . import helpers


MAX_DELIVERY_FORMS = 20


@permission_required('core.can_store')
def delivery(req):
    through_storage = Storage.objects.filter(type='through').first()
    storages = Storage.objects.all()
    orders = Order.objects.filter(
        complete=False, sent__isnull=False
    ).order_by('-sent')
    ctx = dict(title=_('Delivery'), ts=through_storage, storages=storages,
               storage=None, orders=orders, places=None)
    storage_id = int(req.GET.get('storage', 0))
    if storage_id:
        ctx['storage'] = Storage.objects.get(pk=storage_id)
        ctx['places'] = StoragePlace.objects.filter(storage=ctx['storage'])
    return render(req, 'core/storage/delivery.html', ctx)


@permission_required('core.can_store')
def delivery_store_packages(req):
    get_form = DeliverOrderForm(req.GET)
    storage = req.GET.get('storage')
    packages = []
    if get_form.is_valid():
        cd = get_form.cleaned_data
        packages = helpers.store_packages(cd['delivered'], cd['order'],
                                          cd['place'], req.user)
    else:
        messages.error(req, _('Something went wrong.'))
        return redirect('core:delivery')
    ctx = dict(title=_('Delivery'), packages=packages, storage=storage,
               log=packages[0].stored_chemical.chemical.special_log,
               ref=packages[0], comp=COMPOSITION_CHOICES,
               cont=CONTAINER_MATERIAL_CHOICES, mass=MASS_CHOICES)
    return render(req, 'core/storage/deliver_packages.html', ctx)


@permission_required(('core.inventory', 'core.can_store'))
def deliver_box(req):
    if req.method == 'POST':
        count = req.POST.get('package_count')
        data = req.POST.getlist('packages')
        form = InitialDeliveryForm(req.POST, req.FILES)
        packages = []
        if form.is_valid():
            cd = form.cleaned_data
            additional = helpers.get_additional_packages(
                cd['chemical'], count, data
            )
            if helpers.can_store_here(cd['chemical'], cd['place']):
                package = helpers.initial_delivery(req.user, **cd)
                packages.append(package.id)
                for add in additional:
                    cd['brutto_mass'] = add
                    p = helpers.initial_delivery(req.user, **cd)
                    packages.append(p.id)
            else:
                messages.error(
                    req, _('Chemical {} can not be stored in place {}. '
                           'Place/Storage is not lockable!').format(
                        cd['chemical'], cd['place']
                    )
                )
        if packages:
            req.session['new_packages'] = packages
            return redirect('core:delivery-initial-result')
    else:
        form = InitialDeliveryForm()
    ctx = dict(form=form)
    return render(req, 'core/storage/deliver_box.html', ctx)


@permission_required(('core.inventory', 'core.can_store'))
def initial_delivery(req):
    num = int(req.GET.get('num', 12))
    if num > MAX_DELIVERY_FORMS:
        num = MAX_DELIVERY_FORMS
    DeliveryFormSet = formset_factory(InitialDeliveryForm, extra=num,
                                      max_num=MAX_DELIVERY_FORMS)
    if req.method == 'POST':
        formset = DeliveryFormSet(req.POST, req.FILES)
        packages = []
        for form in formset:
            if form.is_valid():
                cd = form.cleaned_data
                if helpers.can_store_here(cd['chemical'], cd['place']):
                    package = helpers.initial_delivery(req.user, **cd)
                    packages.append(package.id)
                else:
                    messages.error(
                        req, _('Chemical {} can not be stored in place {}. '
                               'Place/Storage is not lockable!').format(
                            cd['chemical'], cd['place']
                        )
                    )
        if packages:
            req.session['new_packages'] = packages
            return redirect('core:delivery-initial-result')
    else:
        formset = DeliveryFormSet()
    try:
        del req.session['new_packages']
    except KeyError:
        pass
    ctx = dict(title=_('Initial Delivery'), num=num,
               formset=formset, max_forms=MAX_DELIVERY_FORMS)
    return render(req, 'core/storage/initial_delivery.html', ctx)


@permission_required(('core.inventory', 'core.can_store'))
def initial_delivery_result(req):
    package_ids = req.session.get('new_packages', [])
    if not package_ids:
        messages.error(req, _('No new packages found.'))
        return redirect('core:index')
    packages = StoredPackage.objects.select_related().filter(
        id__in=package_ids
    ).order_by('stored_chemical__chemical__name')
    ctx = dict(title=_('Result'), packages=packages)
    return render(req, 'core/storage/initial_delivery_result.html', ctx)


@permission_required('core.can_order')
def new_order_old_package(req, package_id):
    package = StoredPackage.objects.get(pk=int(package_id))
    if settings.USE_OZONE:
        # Render Ozone order form here
        pass
    else:
        pass
    return HttpResponse(str(package))


@login_required
def info_orders(req):
    choice = req.GET.get('filter', 'open')
    query = Order.objects.all()
    if choice == 'open':
        orders = query.filter(complete=False, sent__isnull=False)
    else:
        last_year = date.today() - timedelta(days=365)
        orders = query.filter(complete=True, stored__date__gt=last_year)
    ctx = dict(title=_('Info Orders'), orders=orders.order_by('-stored'),
               choice=choice)
    return render(req, 'core/storage/info_orders.html', ctx)


def chems_of_supplier(req, sid):
    company = Company.objects.get(pk=int(sid))
    _codes = Barcode.objects.filter(stored_chemical__company=company)
    codes = []
    for c in _codes.order_by('chemical__name'):
        c.order_count = 0
        for o in c.orders.all():
            c.order_count += o.count
        codes.append(c)
    ctx = dict(title=_('Supplier'), codes=codes, company=company)
    return render(req, 'core/storage/info_supplier.html', ctx)


# API

@permission_required('core.can_store')
def api_delivery(req):
    barcode = req.GET.get('barcode', '').strip()
    storage_id = int(req.GET.get('storage'))
    storage = Storage.objects.get(pk=storage_id)
    bc = Barcode.objects.filter(code=barcode).first()
    data = dict(success=False)
    if bc is not None:
        orders = bc.orders.filter(complete=False, sent__isnull=False)
        if not orders:
            data['html'] = _('No orders found for this barcode.')
        else:
            ctx = dict(bc=bc, places=storage.places.all(),
                       orders=orders.order_by('-sent'), storage=storage)
            data['html'] = render_to_string(
                req, 'core/storage/delivery.part.html', ctx
            )
            data['success'] = True
    else:
        data['html'] = _('No data found for this barcode.')
    return render_json(req, data)


@permission_required('core.can_store')
def api_store_fast(req):
    form = DeliverOrderForm(req.GET)
    if form.is_valid():
        cd = form.cleaned_data
        helpers.store_packages(cd['delivered'], cd['order'], cd['place'],
                               req.user)
        success = True
    else:
        success = False
    return render_json(req, {'success': success})


@csrf_exempt
@login_required
def api_store_extra(req):
    form = DeliverJSONForm(req.POST)
    if form.is_valid():
        cd = form.cleaned_data
        p = cd['package']
        p.composition = cd['composition']
        p.container_material = cd['container']
        p.supplier_batch = cd.get('batch', '')
        p.best_before = cd.get('best_before', None)
        if p.stored_chemical.chemical.special_log:
            p.brutto_mass = cd['brutto']
            p.brutto_mass_unit = cd['brutto_unit']
        p.save()
        success = True
    else:
        success = False
    return render_json(req, {'success': success})
