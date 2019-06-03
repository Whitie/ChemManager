# -*- coding: utf-8 -*-

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _

from .. import units
from ..forms import NewNormalPackageForm, NewSpecialPackageForm, EXP_LOOKUP
from ..models import Chemical
from ..models.storage import (
    PackageUsage, StoredPackage, MaterialSafetyDataSheet,
    StoredChemical, InventoryDifference, StockLimit
)


MO = Decimal(-1)
INV_NOTE = _('Inventory balancing!')


def search_chemical_by_name(search):
    query = (
        Q(name__icontains=search) | Q(name_en__icontains=search) |
        Q(iupac_name__icontains=search) | Q(iupac_name_en__icontains=search) |
        Q(formula__icontains=search) | Q(synonyms__name__icontains=search) |
        Q(identifiers__cas__startswith=search)
    )
    chems = []
    for chem in Chemical.objects.select_related().filter(
      query, active=True).order_by('name'):
        if chem not in chems:
            chems.append(chem)
    return chems


def search_package(data):
    query = (
        Q(stored_chemical__chemical=data['chemical']) &
        Q(stored_chemical__chemical__active=True)
    )
    readable = [_('Chemical = {}').format(data['chemical'].display_name)]
    if data['storage']:
        query &= Q(place__storage=data['storage'])
        readable.append(_('Storage = {}').format(data['storage'].name))
    if data['department']:
        query &= Q(place__storage__department=data['department'])
        readable.append(_('Department = {}').format(data['department']))
    if data['content']:
        exp = EXP_LOOKUP[data['exp']]
        content, unit = units.get_default(data['content'], data['unit'])
        query &= Q(**{'content_default__{}'.format(data['exp']): content})
        readable.append(_('Content {exp} {value} {unit}').format(
            exp=exp, value=content, unit=unit
        ))
    if data['composition']:
        query &= Q(composition=data['composition'])
        readable.append(_('Composition = {}').format(data['composition']))
    if data['container_material']:
        query &= Q(container_material=data['container_material'])
        readable.append(_('Container Material = {}').format(
            data['container_material']
        ))
    q = StoredPackage.objects.select_related().filter(query).order_by(
        'place__storage__department__name', 'place__storage__name'
    )
    return q, readable


def get_packages_for_chemical(chem):
    packages = []
    for stored in chem.storage.select_related().all():
        for package in stored.packages.select_related().filter(empty=False):
            packages.append(package)
    return packages


def check_for_old_packages(package, storage):
    return StoredPackage.objects.filter(
        stored_chemical=package.stored_chemical, place__storage=storage,
        empty=False
    ).exclude(pk=package.id)


def handle_consumption(req, storage, package):
    old = check_for_old_packages(package, storage)
    if len(old) > 1:
        req.session['old_packages'] = [x.id for x in old]
        req.session['storage_id'] = storage.id
        return redirect('core:package-remove')
    elif len(old) == 1:
        old_package = StoredPackage.objects.select_related().get(pk=old[0].id)
        data = {'reason': ugettext('Automatic removal'),
                'task': '-'}
        dispose_package(old_package, req.user, data)
        msg = _('Package [{}] was automatically removed').format(old_package)
        messages.success(req, msg)
    else:
        messages.info(req, _('No old package found. Nothing removed.'))
    return redirect('core:package-info', pid=package.id)


def dispose_package(package, user, data):
    stock = package.get_inventory()
    package.empty = True
    package.disposed_by = user
    package.dispose_reason = data['reason']
    package.save()
    use = PackageUsage(
        package=package, user=user, used_by=user, task=data['task'],
        mass_after=None, removed_quantity=stock.value,
        removed_quantity_unit=stock.unit
    )
    use.save()


def store_msds(memfile, published=None):
    if published is None:
        published = timezone.now().date()
    msds = MaterialSafetyDataSheet.objects.create(
        published=published, document=memfile
    )
    msds.save()
    return msds


def get_ref_msds(chem):
    try:
        if chem.identifiers.imported_from:
            fp = chem.identifiers.imported_from
            return MaterialSafetyDataSheet.objects.create(
                document=fp, published=chem.added.date()
            )
        else:
            return None
    except:
        pass


def store_chemical(chem, data):
    if data['msds']:
        msds = store_msds(data['msds'], data.get('published', None))
    elif data['old_msds']:
        msds = MaterialSafetyDataSheet.objects.get(pk=data['old_msds'])
    else:
        msds = get_ref_msds(chem)
    stored, _ = StoredChemical.objects.get_or_create(
        chemical=chem, company=data['company'], quality=data['quality'],
        name_extra=data['name_extra']
    )
    if msds is not None:
        stored.msds = msds
    stored.save()
    return stored


def initial_delivery(user, chemical, **data):
    data['old_msds'] = None
    stored = store_chemical(chemical, data)
    package = StoredPackage(
        stored_chemical=stored, place=data['place'], content=data['content'],
        unit=data['unit'], composition=data['composition'],
        container_material=data['container_material'],
        supplier_ident=data['supplier_ident'],
        supplier_code=data['supplier_code'],
        supplier_batch=data['supplier_batch'],
        best_before=data['best_before'], stored_by=user
    )
    if data['brutto_mass']:
        package.brutto_mass = data['brutto_mass']
        package.brutto_mass_unit = data['brutto_mass_unit']
    package.save()
    return package


def get_package_form(chem, storage, data=None):
    if chem.special_log:
        Form = NewSpecialPackageForm
    else:
        Form = NewNormalPackageForm
    if data is None:
        return Form(storage)
    else:
        return Form(storage, data)


def get_threshold(unit):
    if units.is_mass(unit):
        return settings.SHOW_THRESHOLDS['mass']
    else:
        return settings.SHOW_THRESHOLDS['vol']


def check_removal(package, inv, remove, remove_unit):
    """Checks if a removal is correct."""
    current = inv
    to_remove = units.make_unit(remove, remove_unit)
    threshold = get_threshold('g')
    if isinstance(to_remove, units.Volume):
        tmp = units.volume_to_mass(to_remove.value, to_remove.unit,
                                         package.stored_package.chemical)
        to_remove = units.make_unit(tmp, 'g')
    if isinstance(current, units.Volume):
        tmp = units.volume_to_mass(current.value, current.unit,
                                       package.stored_chemical.chemical)
        current = units.make_unit(tmp, 'g')
    if current >= to_remove:
        if (current - to_remove) <= threshold:
            package.empty = True
            package.save()
        return True
    return False


def _check_empty(package):
    threshold = get_threshold(package.unit)
    if package.get_inventory() <= threshold:
        package.empty = True
        package.save()
        return True
    return False


def _save_to_db(diff, data, user):
    usage = abs(diff)
    threshold = get_threshold(usage.unit)
    InventoryDifference.objects.create(
        package=data['package'], value=diff.value, unit=diff.unit,
        user=user, note=data['note']
    )
    if usage > threshold:
        if diff > threshold:
            diff.value = -diff.value
        PackageUsage.objects.create(
            package=data['package'], removed_quantity=diff.value,
            removed_quantity_unit=diff.unit, used_by=user,
            user=user, task=_('Inventory balancing'), is_inventory=True
        )
        return True
    return False


def _calculate_difference(data):
    if data['ok']:
        return units.make_unit(Decimal(), data['unit'])
    before = units.make_unit(data['old_value'], data['old_unit'])
    current = units.make_unit(data['value'], data['unit'])
    diff = current - before
    inv = data['package'].get_inventory()
    if abs(diff) > inv:
        msg = ugettext('Inventory difference greater than saved stock: '
                       '{} > {}').format(abs(diff), inv)
        raise ValueError(msg)
    return diff


def save_inventory(data, user):
    try:
        diff = _calculate_difference(data)
    except ValueError as err:
        return False, str(err), None
    try:
        if _save_to_db(diff, data, user):
            color = 'orange'
        else:
            color = 'green'
    except Exception as err:
        return False, str(err), None
    msg = ugettext('Data saved. Difference: {}.').format(diff)
    if _check_empty(data['package']):
        msg = ugettext('{} Package marked as empty.').format(msg)
        return True, msg, color
    return True, msg, color


def store_packages(count, order, place, user):
    order.deliver(count)
    bc = order.barcode
    packages = []
    for i in range(count):
        packages.append(
            StoredPackage.objects.create(
                stored_chemical=bc.stored_chemical, place=place,
                content=bc.content, unit=bc.unit, supplier_ident=bc.ident,
                supplier_code=bc.code, stored_by=user
            )
        )
    return packages


def get_usage(data):
    to_date = data['to_date'] + timedelta(days=1)
    if data['group']:
        query = Q(group=data['group'])
    else:
        query = Q(used_by=data['instructor'])
    query &= Q(usage_date__range=(data['from_date'], to_date))
    if data['only_tox']:
        query &= Q(package__stored_chemical__chemical__special_log=True)
    return PackageUsage.objects.select_related().filter(
        query).order_by('-usage_date')


def check_observe(storage, package):
    return check_observe_chemical(storage, package.stored_chemical.chemical)


def check_observe_chemical(storage, chemical, sep=', '):
    own_sc = chemical.storage_class
    if not own_sc:
        return True, _('No storage class given')
    f = dict(storage__packages__place__storage=storage,
             storage__packages__empty=False)
    query = Chemical.objects.select_related().filter(**f)
    restrictions = []
    for chem in query.exclude(id=chemical.id).distinct():
        sc = chem.storage_class
        if sc:
            restriction = sc.can_store_with(own_sc)
            if not restriction:
                return False, _(
                    '{sc} -> Storage of {new} together with {stored} is '
                    'possibly not allowed. Check storage classes and stored '
                    'masses.'
                ).format(sc=sc.value, new=chem, stored=chemical)
            else:
                text = '{sc} -> {restr}'.format(sc=sc.value,
                                                restr=restriction.text)
                restrictions.append(text)
    return True, sep.join(restrictions)


def get_inventory_for_storage(chemical, storage):
    stocks = []
    query = dict(chemical=chemical, packages__place__storage=storage,
                 packages__empty=False)
    for stchem in StoredChemical.objects.filter(**query).distinct():
        stocks.append(stchem.get_inventory_for_storage(storage))
    if not stocks:
        return units.Mass(0, 'g')
    start = stocks[0]
    for s in stocks[1:]:
        start += s
    return start


def get_stocklimit(chemical, storage, type='min', unit='g'):
    limit = StockLimit.objects.filter(chemical=chemical, storage=storage,
                                      type=type).first()
    if limit is not None:
        return limit.obj


def set_limit(chem, storage, _type, value, unit):
    if value:
        limit = StockLimit.objects.filter(
            chemical=chem, storage=storage, type=_type
        ).first()
        if limit is None:
            limit = StockLimit(chemical=chem, storage=storage, type=_type)
        limit.stock = Decimal(value)
        limit.unit = unit
        limit.save()
        res = str(limit.obj)
    else:
        limit = StockLimit.objects.filter(
            chemical=chem, storage=storage, type=_type
        ).first()
        if limit is not None:
            res = str(limit.obj)
        else:
            res = _('not set')
    return res


def merge_packages(fill, remove, user):
    data = {
        'task': ugettext('Transfer'),
        'reason': ugettext('Content transfered to {fill}').format(
            fill=fill.package_id)
    }
    content = fill.blank_obj
    for p in remove:
        stock = p.get_inventory()
        content += stock
        dispose_package(p, user, data)
        PackageUsage.objects.create(
            package=fill, removed_quantity=-stock.value,
            removed_quantity_unit=stock.unit, used_by=user,
            user=user, task=_('Filled up from {}').format(p.package_id)
        )
    return content


def can_store_here(chem, place):
    if chem.special_log:
        if place.for_tox:
            return True
        else:
            return False
    return True
