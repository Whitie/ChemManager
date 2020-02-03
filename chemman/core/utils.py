# -*- coding: utf-8 -*-

import base64
import string

from decimal import Decimal
from hashlib import md5

import qrcode

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render as django_render
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from qrcode.image.svg import SvgPathFillImage

from .json_utils import dumps, loads
from .models.base import ListCache
from .models.safety import GHSPictogram, HazardStatement


FIELD_TYPES = {
    'molar_mass': Decimal,
    'storage_temperature': int,
    'whc': int,
    'mac': Decimal,
    'mabc': Decimal,
    'pictograms__ref_num': int,
    'physical_data__melting_point_low': Decimal,
    'physical_data__boiling_point_low': Decimal,
}
QR_ERROR_CORRECTION = {
    'L': 1,
    'M': 0,
    'Q': 3,
    'H': 2,
}


class Menu:

    def __init__(self, name, *items):
        self.name = name
        self.items = list(items)

    def __iter__(self):
        for item in self.items:
            yield item.href, item.text

    def add(self, item):
        self.items.append(item)

    def insert(self, item, position=0):
        self.items.insert(position, item)


class MenuItem:

    def __init__(self, text, urlname=None, url=None):
        self.text = text
        self.urlname = urlname
        self.url = url

    @property
    def href(self):
        if self.url is None:
            self.url = reverse(self.urlname)
        return self.url


# Main ChemManager menus (extend with menu variable in context)
base_menu = Menu(
    _('Menu'),
    MenuItem(_('Information'), urlname='core:info'),
    MenuItem(_('Lists'), urlname='core:choose-list'),
    MenuItem(_('Storage'), urlname='core:storage-index'),
    MenuItem(_('Management'), urlname='core:manage'),
    MenuItem(_('Handbooks'), urlname='core:hb-overview'),
)
action_menu = Menu(
    _('Actions'),
    MenuItem(_('Extended Search'), urlname='core:ext-search'),
    MenuItem(_('Consume'), urlname='core:consume-select'),
    MenuItem(_('Delivery'), urlname='core:delivery'),
)
if settings.PRESENTATION_URL:
    item = MenuItem(_('Presentations'), url=settings.PRESENTATION_URL)
    base_menu.add(item)
menus = (base_menu, action_menu)


def is_active(app):
    """Check if an application is in settings.INSTALLED_APPS."""
    from django.conf import settings
    return app in settings.INSTALLED_APPS


def render(request, template_name, context=None, content_type=None,
           status=None, using=None):
    ctx = context or {}
    _menus = list(menus)
    if 'menu' in ctx:
        _menus = [_menus[0]]
        m = ctx.pop('menu')
        if isinstance(m, list):
            _menus.extend(m)
        else:
            _menus.append(m)
    ctx['menus'] = _menus
    return django_render(request, template_name, ctx, content_type, status,
                         using)


def render_to_string(request, template_name, context=None):
    template = get_template(template_name)
    return template.render(context, request)


def render_json(req, obj):
    return JsonResponse(obj, safe=False)


def str2num(name, val):
    if name in FIELD_TYPES:
        try:
            return FIELD_TYPES[name](val.replace('.', ','))
        except:
            return val
    return val


def _get_range(dct):
    numbers = []
    for k in dct:
        if k.startswith('field_'):
            numbers.append(int(k.split('_')[-1]))
    return max(numbers)


def form_to_json(cleaned_data):
    cd = cleaned_data
    name = cd['name'].strip()
    data = {
        'query': {
            '{}__{}'.format(cd['field_1'], cd['exp_1']):
                str2num(cd['field_1'], cd['term_1'])
        },
        'and': [],
        'or': [],
    }
    highest = _get_range(cd)
    for i in range(2, highest + 1):
        term = cd.get('term_{}'.format(i), '').strip()
        if term:
            field = cd.get('field_{}'.format(i))
            exp = cd.get('exp_{}'.format(i))
            andor = cd.get('andor_{}'.format(i))
            data[andor].append(
                {'{}__{}'.format(field, exp): str2num(field, term)}
            )
    return data, name


def form_to_paramstring(cleaned_data):
    data, name = form_to_json(cleaned_data)
    s = dumps(data).encode('utf-8')
    h = md5(s).hexdigest()
    if name:
        lc, created = ListCache.objects.get_or_create(hash=h)
        if created:
            lc.name = name
            lc.json_query = data
        lc.save()
    return base64.b64encode(s).decode('ascii'), name or _('List')


def dict_to_query(data):
    if 'active' not in data['query']:
        data['query']['active'] = True
    query = Q(**data['query'])
    for q in data['or']:
        query |= Q(**q)
    for q in data['and']:
        query &= Q(**q)
    return query


def paramstring_to_query(param):
    s = base64.b64decode(param.encode('ascii'))
    data = loads(s.decode('utf-8'))
    query = dict_to_query(data)
    return query


def validate_cas(cas_num):
    cas, check = cas_num.strip().rsplit('-', 1)
    cas = cas.replace('-', '')
    checksum = 0
    for pos, num in enumerate(reversed(cas), 1):
        checksum += pos * int(num)
    return str(checksum)[-1] == check.strip()


def validate_ecn(ec_num):
    ec, check = ec_num.strip().rsplit('-', 1)
    ec = ec.replace('-', '')
    checksum = 0
    for pos, num in enumerate(ec, 1):
        checksum += pos * int(num)
    check_digit = checksum % 11
    return check_digit == int(check)


def first_letter(s):
    s = s.lower()
    for c in s:
        if c in string.ascii_lowercase:
            return c
    return 'undefined'


def structure_path(instance, filename):
    return 'structures/{}/{}'.format(first_letter(instance.name), filename)


def make_qrcode(image_format, data, box_size=10, border=4,
                error_correction='Q'):
    imf = image_format.lower()
    if border < 4:
        border = 4
    correction = QR_ERROR_CORRECTION.get(error_correction.upper(), 3)
    qrc = qrcode.QRCode(
        version=None,
        error_correction=correction,
        box_size=box_size,
        border=border
    )
    qrc.add_data(data)
    qrc.make(fit=True)
    if imf == 'svg':
        qrc.image_factory = SvgPathFillImage
        content_type = 'image/svg+xml'
    else:
        content_type = 'image/png'
    return qrc.make_image(), content_type


def check_cmr(chem):
    if chem.cmr:
        chem.special_log = True
        return
    for base in settings.CMR_HAZARDS:
        query = HazardStatement.objects.filter(ref__startswith=base)
        for h in query:
            if h in chem.hazard_statements.all():
                chem.special_log = True
                chem.cmr = True
                break
        if chem.cmr:
            break


def check_toxic(chem):
    if chem.special_log:
        return
    pic = GHSPictogram.objects.get(ref_num=6)
    if pic in chem.pictograms.all():
        chem.special_log = True


def check_flammable(chem):
    if (
        hasattr(chem, 'physical_data') and
        chem.physical_data.physical_state == 'l'
    ):
        pic = GHSPictogram.objects.get(ref_num=2)
        if pic in chem.pictograms.all():
            chem.flammable = True
