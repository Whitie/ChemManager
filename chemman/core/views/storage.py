# -*- coding: utf-8 -*-

import csv
import os

from collections import OrderedDict
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from ..forms import (
    NewPackageForm, DisposeForm, ConsumeNormalForm, ConsumeSpecialForm,
    InventoryJSONForm, ToxActionForm
)
from ..models import Chemical, Department, OperatingInstruction
from ..models.safety import StorageClass
from ..models.storage import (
    Building, StockLimit, Storage, StoredChemical, StoredPackage,
    LegalLimit, StoragePlace, PackageUsage,
    MASS_CHOICES, VOLUME_CHOICES
)
from ..utils import render, render_json
from .. import units
from . import helpers


_raise = os.urandom(20)


def get_choices(unit):
    if units.is_mass(unit):
        return MASS_CHOICES
    else:
        return VOLUME_CHOICES


def package_info(req, pid):
    package = StoredPackage.objects.select_related().get(pk=int(pid))
    chem = package.stored_chemical.chemical
    ctx = dict(title=_('Package Info'), package=package, chem=chem,
               inventory=package.get_inventory())
    return render(req, 'core/storage/package_info.html', ctx)


def package_info_by_uid(req, package_id):
    pk = int(package_id.split('-')[-1])
    return package_info(req, pk)


def chem_inventory(req, chem_id):
    # Inventory for one chemical (all storage places)
    chem = Chemical.objects.select_related().get(pk=chem_id)
    packages = StoredPackage.objects.select_related().filter(
        stored_chemical__id__in=chem.storage.all(), empty=False
    ).order_by('place__storage', 'stored_chemical__chemical__name')
    sorted_packages = {}
    for p in packages:
        name = p.place.storage
        if name not in sorted_packages:
            dep = name.department
            c = p.stored_chemical.chemical
            sorted_packages[name] = {
                'count': 1, 'inventory': p.get_inventory(),
                'id': p.stored_chemical.id,
                'opinst': OperatingInstruction.objects.filter(
                    chemical=c, department=dep
                )
            }
        else:
            sorted_packages[name]['count'] += 1
            sorted_packages[name]['inventory'] += p.get_inventory()
    max_limits = LegalLimit.objects.filter(chemicals=chem, type='max')
    min_limits = LegalLimit.objects.filter(chemicals=chem, type='min')
    ctx = dict(title=_('Storage of {}').format(chem.name), chem=chem,
               packages=packages, max_limits=max_limits,
               min_limits=min_limits, sorted_packages=sorted_packages)
    return render(req, 'core/storage/chem_info.html', ctx)


def storage_inventory(req, storage_id):
    # Inventory for one storage (all chemicals/packages)
    storage = Storage.objects.select_related().get(pk=storage_id)
    pids = []
    for place in StoragePlace.objects.filter(storage=storage):
        for package in StoredPackage.objects.filter(place=place, empty=False):
            pids.append(package.id)
    req.session['new_packages'] = pids
    ctx = dict(title=_('Storage {}').format(storage.name),
               storage=storage)
    return render(req, 'core/storage/storage.html', ctx)


def storage_index(req):
    buildings = Building.objects.select_related().all()
    ctx = dict(title=_('Storage'), buildings=buildings)
    try:
        del req.session['new_packages']
    except KeyError:
        pass
    return render(req, 'core/storage/index.html', ctx)


def storage_classes_info(req):
    storage_classes = []
    for sc in StorageClass.objects.all().order_by('id'):
        sc.stored_chems = StoredChemical.objects.filter(
            chemical__storage_class=sc
        ).count()
        sc.info = sc.get_store_with_classes()
        sc.spec = {'query': {'storage_class__id': sc.id}, 'and': [], 'or': []}
        storage_classes.append(sc)
    ctx = dict(title=_('Storage Classes'), classes=storage_classes)
    return render(req, 'core/storage/classes_info.html', ctx)


def info_stored_chemicals(req):
    chems = []
    ids = []
    for chem in Chemical.objects.select_related().all().order_by('name'):
        if chem.has_inventory:
            chems.append(chem)
            ids.append(str(chem.id))
    ctx = dict(title=_('Stored Chemicals'), chems=chems, ids=ids,
               thresholds=settings.SHOW_THRESHOLDS)
    return render(req, 'core/storage/stored_chemicals.html', ctx)


@login_required
def check_observe(req, storage_id):
    storage = Storage.objects.select_related().get(pk=storage_id)
    chems = Chemical.objects.select_related().filter(
        storage__packages__place__storage=storage,
        storage__packages__empty=False
    ).distinct()
    ctx = dict(title=_('Observation'), storage=storage, chems=chems)
    return render(req, 'core/storage/observe.html', ctx)


@login_required
def info_tox_usage(req):
    ctx = dict(title=_('Usage'), submitted=False)
    if req.method == 'POST':
        form = ToxActionForm(req.POST)
        if form.is_valid():
            ctx['submitted'] = True
            ctx.update(form.cleaned_data)
            ctx['usages'] = helpers.get_usage(form.cleaned_data)
    else:
        initial = {
            'from_date': timezone.now().date() - timedelta(days=90),
            'to_date': timezone.now().date(),
            'only_tox': True
        }
        form = ToxActionForm(initial=initial)
    ctx['form'] = form
    return render(req, 'core/storage/tox_info.html', ctx)


def packages_history(req):
    _filter = req.GET.get('filter', 'all')
    all_packages = StoredPackage.objects.select_related().all()
    if _filter == 'tox':
        all_packages = all_packages.filter(
            stored_chemical__chemical__special_log=True
        )
    current = all_packages.filter(empty=False)
    old = all_packages.filter(empty=True)
    ctx = dict(title=_('History of Packages'), current=current, old=old,
               tox=_filter == 'tox')
    return render(req, 'core/storage/history.html', ctx)


@permission_required('core.can_dispose')
def dispose(req, package_id):
    package = StoredPackage.objects.select_related().get(pk=package_id)
    stock = package.get_inventory()
    chem = package.stored_chemical.chemical
    if req.method == 'POST':
        form = DisposeForm(req.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cd['task'] = ugettext('Disposal')
            helpers.dispose_package(package, req.user, cd)
            messages.success(req,
                             _('{} where marked as disposed').format(stock))
            return redirect('core:package-info', pid=package.id)
    else:
        form = DisposeForm()
    chem = package.stored_chemical.chemical
    ctx = dict(title=_('DISPOSE'), package=package, chem=chem, form=form,
               stock=stock)
    return render(req, 'core/storage/dispose.html', ctx)


@permission_required('core.can_transfer')
def transfer(req, package_id):
    package = StoredPackage.objects.select_related().get(pk=package_id)
    if req.method == 'POST':
        new_place = int(req.POST.get('places', 0))
        if new_place:
            place = StoragePlace.objects.select_related().get(pk=new_place)
            if helpers.can_store_here(package.chemical, place):
                storage = place.storage
                can_store = True
                msg = ''
                if storage.observe:
                    can_store, msg = helpers.check_observe(storage, package)
                    if not can_store and settings.OBSERVE_AND_WARN:
                        # Maybe block storing here in the future, if the
                        # storage has observe set to True
                        messages.warning(req, msg)
                package.place = place
                package.stored_by = req.user
                package.save()
                if place.storage.consumption:
                    return helpers.handle_consumption(req, storage, package)
                return redirect('core:package-info', pid=package.id)
            else:
                messages.error(
                    req, _('Chemical {} can not be stored in place {}. '
                           'Place/Storage is not lockable!').format(
                            package.chemical, place
                    )
                )
    ctx = dict(title=_('Transfer'), package=package)
    return render(req, 'core/storage/transfer.html', ctx)


@permission_required('core.can_transfer')
def merge_packages(req, storage_id, chem_id):
    storage = Storage.objects.get(pk=storage_id)
    chem = Chemical.objects.get(pk=chem_id)
    packages = StoredPackage.objects.filter(
        place__storage=storage, stored_chemical__chemical=chem,
        empty=False
    )
    if packages.count() <= 1:
        messages.error(req, _('Not enough packages to merge!'))
        return redirect('core:storage-inventory', storage_id=storage.id)
    ctx = dict(title=_('Merge packages'), chem=chem, packages=packages,
               storage=storage)
    return render(req, 'core/storage/merge.html', ctx)


@permission_required('core.can_transfer')
def get_merge_packages(req):
    pids = req.GET.getlist('packages[]')
    packages = StoredPackage.objects.filter(id__in=map(int, pids))
    ctx = dict(packages=packages)
    return render(req, 'core/storage/merge_select.part.html', ctx)


@permission_required('core.can_transfer')
def do_merge(req):
    to_remove_ids = req.GET.getlist('remove[]')
    fillup_id = req.GET.get('fillup')
    to_remove = StoredPackage.objects.filter(id__in=map(int, to_remove_ids))
    fillup = StoredPackage.objects.get(pk=int(fillup_id))
    moved = helpers.merge_packages(fillup, to_remove, req.user)
    ctx = dict(filled=fillup, removed=to_remove, moved=moved)
    return render(req, 'core/storage/merge_result.part.html', ctx)


@login_required
def choose_removal(req):
    ids = req.session.get('old_packages', [])
    packages = StoredPackage.objects.filter(id__in=ids)
    if req.method == 'POST':
        storage_id = req.session.get('storage_id')
        to_remove = req.POST.getlist('packages')
        if to_remove:
            StoredPackage.objects.filter(id__in=map(int, to_remove)).delete()
            messages.success(req, _('Package(s) removed'))
        else:
            messages.info(req, _('Nothing removed'))
        del req.session['old_packages']
        del req.session['storage_id']
        return redirect('core:storage-inventory', storage_id=storage_id)
    ctx = dict(title=_('Remove package'), packages=packages)
    return render(req, 'core/storage/choose_removal.html', ctx)


@permission_required('core.can_store')
def store_new_package(req, chem_id):
    chem = Chemical.objects.select_related().get(pk=chem_id)
    if req.method == 'POST':
        form = NewPackageForm(chem, req.POST, req.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            stored_chem = helpers.store_chemical(chem, cd)
            return redirect(
                'core:package-new', stored_chem_id=stored_chem.id,
                storage_id=cd['storage'].id
            )
    else:
        form = NewPackageForm(chem)
    ctx = dict(title=_('New Package'), chem=chem, form=form)
    return render(req, 'core/storage/new_package.html', ctx)


@permission_required('core.can_store')
def store_new_package_2(req, stored_chem_id, storage_id):
    stored = StoredChemical.objects.select_related().get(
        pk=stored_chem_id
    )
    storage = Storage.objects.select_related().get(pk=storage_id)
    if req.method == 'POST':
        form = helpers.get_package_form(stored.chemical, storage, req.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cd['stored_chemical'] = stored
            cd['stored_by'] = req.user
            package = StoredPackage.objects.create(**cd)
            messages.success(req, _('Package {} was saved.').format(package))
            if storage.consumption:
                return helpers.handle_consumption(req, storage, package)
            can_store, msg = helpers.check_observe(storage, package)
            if not can_store and settings.OBSERVE_AND_WARN:
                # Maybe block storing here in the future, if the storage
                # has observe set to True
                messages.warning(req, msg)
            return redirect('core:package-info', pid=package.id)
    else:
        form = helpers.get_package_form(stored.chemical, storage)
    ctx = dict(title=_('New Package'), stored=stored, storage=storage,
               form=form, no_comp=_('No company choosen'))
    return render(req, 'core/storage/new_package_2.html', ctx)


@permission_required('core.can_consume')
def select_chemical_for_consume(req):
    if req.method == 'POST':
        _package_id = req.POST['package_id'].strip()
        if _package_id:
            req.session['fullpid'] = _package_id
            package_id = int(_package_id.split('-')[-1])
            return redirect('core:consume', package_id=package_id)
    ctx = dict(title=_('Consume selection'))
    return render(req, 'core/storage/consume/select.html', ctx)


def consume_special(req, package, inv):
    initial = dict(removed_quantity_unit=inv.unit)
    if req.method == 'POST':
        form = ConsumeSpecialForm(req.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cd['package'] = package
            usage = PackageUsage.objects.create(user=req.user, **cd)
            if helpers.check_removal(package, inv, usage.removed_quantity,
                                     usage.removed_quantity_unit):
                messages.success(
                    req, _('Consume of {mass} was saved.').format(
                        mass=usage.removed_mass
                    ))
                if package.empty:
                    messages.info(
                        req, _('Package was marked as empty.')
                    )
                return redirect('core:package-info', pid=package.id)
            else:
                messages.error(
                    req, _('Consume of {mass} is higher as package inventory '
                           '{inv}.').format(mass=usage.removed_mass, inv=inv)
                )
                usage.delete()
    else:
        form = ConsumeSpecialForm(initial=initial)
    ctx = dict(title=_('Toxic Consume'), package=package, form=form,
               consume_all=inv.value)
    return render(req, 'core/storage/consume/special.html', ctx)


def consume_normal(req, package, inv):
    initial = dict(removed_quantity_unit=inv.unit)
    if req.method == 'POST':
        form = ConsumeNormalForm(req.POST)
        form.fields['removed_quantity_unit'].choices = get_choices(
            package.unit
        )
        if form.is_valid():
            cd = form.cleaned_data
            cd['package'] = package
            usage = PackageUsage(user=req.user, **cd)
            usage.stored_by = req.user
            usage.save(force_insert=True)
            if helpers.check_removal(package, inv, usage.removed_quantity,
                                     usage.removed_quantity_unit):
                messages.success(
                    req, _('Consume of {mass} was saved.').format(
                        mass=usage.removed_mass
                    ))
                if package.empty:
                    messages.info(
                        req, _('Package was marked as empty.')
                    )
                return redirect('core:package-info', pid=package.id)
            else:
                messages.error(
                    req, _('Consume of {mass} is higher as package inventory '
                           '{inv}.').format(mass=usage.removed_mass, inv=inv)
                )
                usage.delete()
    else:
        form = ConsumeNormalForm(initial=initial)
        form.fields['removed_quantity_unit'].choices = get_choices(
            package.unit
        )
    ctx = dict(title=_('Consume'), package=package, form=form,
               consume_all=inv.value)
    return render(req, 'core/storage/consume/normal.html', ctx)


@permission_required('core.can_consume')
def consume(req, package_id):
    try:
        package = StoredPackage.objects.select_related().get(
            pk=package_id
        )
    except StoredPackage.DoesNotExist:
        messages.error(
            req, _('Package with ID {pid} does not exist!').format(
                pid=req.session.get('fullpid', package_id))
        )
        return redirect('core:consume-select')
    inv = package.get_inventory()
    if package.stored_chemical.chemical.special_log:
        return consume_special(req, package, inv)
    else:
        return consume_normal(req, package, inv)


@permission_required('core.inventory')
def make_inventory(req, storage_id):
    storage = Storage.objects.select_related().get(pk=storage_id)
    if req.method == 'POST':
        try:
            helpers.save_inventory(req.POST, req.user)
            return redirect('core:storage-inventory-result',
                            storage_id=storage_id)
        except ValueError as err:
            messages.error(req, str(err))
    ctx = dict(title=_('Make Inventory'), storage=storage,
               places=storage.places.all(), mass=MASS_CHOICES,
               vol=VOLUME_CHOICES)
    return render(req, 'core/storage/inventory.html', ctx)


@login_required
def inventory_result(req, storage_id):
    storage = Storage.objects.select_related().get(pk=storage_id)
    diffs = OrderedDict()
    for place in storage.places.all():
        diffs[place] = OrderedDict()
        for package in StoredPackage.objects.select_related(
          ).filter(place=place).order_by('stored_chemical__chemical__name'):
            diff = package.differences.all().order_by('saved').last()
            if diff is not None:
                diffs[place][package] = diff
    ctx = dict(title=_('Inventory Result'), storage=storage, diffs=diffs)
    return render(req, 'core/storage/inventory_result.html', ctx)


@permission_required('core.can_store')
def print_package_ids(req):
    package_ids = req.session.get('new_packages', [])
    pid = int(req.GET.get('pid', 0))
    if pid:
        package_ids = [pid]
    if not package_ids:
        messages.error(req, _('No packages found.'))
        return redirect('core:index')
    size = int(req.GET.get('size', 50))
    packages = StoredPackage.objects.select_related().filter(
        id__in=package_ids
    ).order_by('stored_chemical__chemical__name')
    ctx = dict(title=_('Print IDs'), packages=packages, size=size, pid=pid)
    return render(req, 'core/storage/print_packages.html', ctx)


@permission_required('core.can_store')
def download_labels_as_csv(req):
    package_ids = req.session.get('new_packages', [])
    pid = int(req.GET.get('pid', 0))
    if pid:
        package_ids = [pid]
    if not package_ids:
        messages.error(req, _('No packages found.'))
        return redirect('core:index')
    packages = StoredPackage.objects.select_related().filter(
        id__in=package_ids
    ).order_by('stored_chemical__chemical__name')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="labels.csv"'
    writer = csv.writer(response, dialect='excel')
    writer.writerow(['ID', 'Name', 'Content'])
    for package in packages:
        name = '{} ({})'.format(
            package.stored_chemical.chemical.display_name,
            package.stored_chemical.get_quality_display()
        )
        if package.stored_chemical.name_extra:
            name = '{}, {}'.format(name, package.stored_chemical.name_extra)
        writer.writerow([package.package_id, name, str(package.content_obj)])
    return response


@permission_required('core.set_limits')
def set_stocklimits(req, storage_id):
    storage = Storage.objects.select_related().get(pk=storage_id)
    chems = OrderedDict()
    for package in StoredPackage.objects.filter(
        place__storage=storage, empty=False
    ).order_by('stored_chemical__chemical__name'):
        chem = package.stored_chemical.chemical
        if chem.id not in chems:
            chems[chem.id] = dict(
                chem=chem, inv=package.get_inventory(), unit=package.unit,
                min=helpers.get_stocklimit(chem, storage, 'min', package.unit),
                max=helpers.get_stocklimit(chem, storage, 'max', package.unit)
            )
        else:
            chems[chem.id]['inv'] += package.get_inventory()
    ctx = dict(title=_('Stocklimits'), storage=storage, chems=chems)
    return render(req, 'core/storage/stocklimits.html', ctx)


# API

@csrf_exempt
def api_inventory_save(req):
    form = InventoryJSONForm(req.POST)
    data = dict(success=False)
    if form.is_valid():
        data['success'], msg, color = helpers.save_inventory(
            form.cleaned_data, req.user
        )
        if data['success']:
            data['message'] = msg
            data['color'] = color
        else:
            data['error'] = msg
    else:
        data['error'] = _('Internal Server Error')
    return render_json(req, data)


def api_get_special_log_list(req):
    data = {}
    for _id, log in Chemical.objects.values_list('id', 'special_log'):
        data[str(_id)] = log
    return render_json(req, data)


def api_inventory_package(req, package_id):
    package = StoredPackage.objects.get(pk=package_id)
    stock = package.get_inventory()
    result = dict(
        value='{:.2f}'.format(stock.value), unit=stock.unit,
        url=reverse('core:package-info', kwargs={'pid': package.id})
    )
    return render_json(req, result)


def api_stock_limit(req, stored_chem_id, storage_id):
    stored_chem = StoredChemical.objects.get(pk=stored_chem_id)
    chem = stored_chem.chemical
    storage = Storage.objects.get(pk=storage_id)
    limit_min = StockLimit.objects.filter(
        chemical=chem, storage=storage, type='min'
    ).first()
    limit_max = StockLimit.objects.filter(
        chemical=chem, storage=storage, type='max'
    ).first()
    ctx = dict(limit_min=limit_min, limit_max=limit_max)
    return render(req, 'core/storage/limit.part.html', ctx)


def api_storages(req, chem_id):
    special_log = Chemical.objects.values_list(
        'special_log', flat=True
    ).get(pk=chem_id)
    storages = {}
    _storages = Storage.objects.select_related().all()
    for s in _storages.order_by('department', 'name'):
        storages[str(s)] = []
        if special_log and s.type != 'through':
            places = s.places.filter(lockable=True)
        else:
            places = s.places.all()
        for p in places:
            storages[str(s)].append(
                {'id': p.id, 'name': p.name}
            )
    return render_json(req, storages)


@csrf_exempt
def api_consume_chem(req):
    search = req.POST.get('search', '')
    query = (
        Q(chemical__name__icontains=search) |
        Q(chemical__name_en__icontains=search) |
        Q(chemical__iupac_name__icontains=search) |
        Q(chemical__iupac_name_en__icontains=search) |
        Q(chemical__formula__icontains=search) |
        Q(chemical__synonyms__name__icontains=search) |
        Q(chemical__identifiers__cas__startswith=search)
    )
    res = []
    tmp = []
    for c in StoredChemical.objects.select_related(
      ).filter(query).order_by('chemical__name'):
        if c not in tmp:
            tmp.append(c)
            res.append({
                'id': c.id,
                'title': str(c),
                'text': 'CAS: {}'.format(c.chemical.identifiers.cas),
            })
    return render_json(req, res)


def api_storage_for_chemical(req):
    stored_chem_id = req.GET['stchemid']
    stchem = StoredChemical.objects.select_related(
        ).get(pk=int(stored_chem_id))
    chem = stchem.chemical
    ois = OrderedDict()
    for dep in Department.objects.all().order_by('name'):
        ois[dep.name] = OperatingInstruction.objects.filter(
            chemical=chem, department=dep
        )
    places = StoragePlace.objects.select_related().filter(
        packages__stored_chemical=stchem).distinct()
    ctx = dict(stchem=stchem, places=places, opinsts=ois, chem=chem)
    return render(req, 'core/storage/select_place.part.html', ctx)


def api_get_packages(req):
    stored_chem_id = req.GET['stchemid']
    place_id = req.GET['place']
    place = StoragePlace.objects.select_related().get(pk=int(place_id))
    stchem = StoredChemical.objects.select_related().get(
        pk=int(stored_chem_id)
    )
    packages = place.packages.filter(stored_chemical=stchem, empty=False)
    ctx = dict(place=place, packages=packages, chem=stchem.chemical)
    return render(req, 'core/storage/select_package.part.html', ctx)


def api_check_observe(req):
    chem_id = int(req.GET.get('chem_id', 0))
    storage_id = int(req.GET.get('storage_id', 0))
    if not chem_id or not storage_id:
        msg = ugettext('Chemical or storage not given.')
        return render_json(req, {'ok': False, 'msg': msg})
    storage = Storage.objects.select_related().get(pk=storage_id)
    chemical = Chemical.objects.select_related().get(pk=chem_id)
    ok, msg = helpers.check_observe_chemical(storage, chemical, '<br>')
    inv = helpers.get_inventory_for_storage(chemical, storage)
    return render_json(req, {'ok': ok, 'msg': str(msg), 'inventory': str(inv)})


@csrf_exempt
def save_stocklimit(req):
    chem_id = int(req.POST.get('chem_id'))
    storage_id = int(req.POST.get('storage_id'))
    chem = Chemical.objects.get(pk=chem_id)
    storage = Storage.objects.get(pk=storage_id)
    if 'reset' in req.POST and req.POST['reset'] == 'yes':
        StockLimit.objects.filter(chemical=chem, storage=storage).delete()
        _min = _('not set')
        _max = _('not set')
    else:
        unit = req.POST.get('unit')
        minimum = req.POST.get('min').strip()
        maximum = req.POST.get('max').strip()
        _min = helpers.set_limit(chem, storage, 'min', minimum, unit)
        _max = helpers.set_limit(chem, storage, 'max', maximum, unit)
    return render_json(req, {'success': True, 'min': _min, 'max': _max})


def api_wrong_brutto(req):
    now = datetime.now()
    try:
        user = User.objects.get(pk=int(req.GET.get('uid')))
        package = StoredPackage.objects.get(pk=int(req.GET.get('pid')))
        # mass = units.Mass(req.GET.get('mass'), req.GET.get('unit'))
        info_to = [
            x.email for x in
            User.objects.filter(username__in=settings.INFO_WRONG_BRUTTO)
            if x.email
        ]
        mail_msg = _(
            'For the package (ID: {pid}) of {chem} was a wrong brutto '
            'mass reported by {user}. The report was filed on {date}.'
            '\n\nThis message was automatically created, please do not '
            'answer.'
        ).format(
            pid=package.package_id, chem=package.chemical,
            user=user.username, date=now.strftime('%d.%m.%Y %H:%M:%S')
        )
        send_mail(
            _('[ChemManager] Wrong brutto mass!'),
            mail_msg,
            settings.DEFAULT_FROM_EMAIL,
            info_to
        )
        msg = _('The following message was send to {}:<br>{}').format(
            ', '.join(info_to), mail_msg
        )
        success = True
    except Exception as e:
        success = False
        msg = _('Error:<br>{}').format(str(e))
    return render_json(req, {'success': success, 'msg': msg})
