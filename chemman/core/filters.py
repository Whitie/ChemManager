# -*- coding: utf-8 -*-

from base64 import b64encode
from os import path

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from jinja2.utils import markupsafe

from . import units
from .json_utils import dumps


BUILTIN_LISTS = {
    'toxic': {
        'name': _('Toxic chemicals (GHS 06)'),
        'query_spec': {
            'query': {'pictograms__ref_num': 6},
            'and': [],
            'or': [],
        }
    },
    'cmr': {
        'name': _('CMR substances'),
        'query_spec': {
            'query': {'cmr': True},
            'and': [],
            'or': [],
        }
    },
}


def markup_unit(value):
    if 'm3' in value:
        return markupsafe.Markup(value.replace('m3', 'm<sup>3</sup>'))
    return value


def list_url(value, name='-'):
    if isinstance(value, dict):
        value = dumps(value)
    param = b64encode(value.encode('utf-8'))
    return reverse('core:list-chemicals',
                   kwargs={'name': name, 'param': param.decode()})


def builtin_list(list_name):
    list_spec = BUILTIN_LISTS[list_name]
    name = list_spec['name']
    tag = '<a href="{url}">{name}</a>'.format(
        url=list_url(list_spec['query_spec'], name), name=name
    )
    return markupsafe.Markup(tag)


def _humanize_mass(value, unit):
    val = units.convert(value, unit, 'g')
    if val >= 1 and val < 1000:
        return '{:.4f} g'.format(val)
    from_unit = 'g'
    if val < 1:
        for u in ('mg', 'µg', 'ng'):
            val = units.convert(val, from_unit, u)
            from_unit = u
            if val >= 1:
                return '{:.4f} {}'.format(val, u)
        return '{:.2f} {}'.format(val, u)
    else:
        for u in ('kg', 't'):
            val = units.convert(val, from_unit, u)
            from_unit = u
            if val < 1000:
                return '{:4f} {}'.format(val, u)
        return '{:4f} {}'.format(val, u)


def _humanize_volume(value, unit):
    val = units.convert(value, unit, 'L')
    print('Liter:', val)
    if val >= 1 and val < 1000:
        return '{:.4f} L'.format(val)
    from_unit = 'L'
    if val < 1:
        for u in ('mL', 'µL'):
            val = units.convert(val, from_unit, u)
            from_unit = u
            if val >= 1:
                return '{:.4f} {}'.format(val, u)
        return '{:.2f} {}'.format(val, u)
    else:
        val = units.convert(val, from_unit, 'm3')
        return markupsafe.Markup('{:4f} m<sup>3</sup>'.format(val))


def humanize_mass_vol(value, unit):
    if value > 1 and value < 1000:
        return '{:.4f} {}'.format(value, markup_unit(unit))
    if unit.lower() in units.TO_GRAMM.keys():
        return _humanize_mass(value, unit)
    elif unit.lower() in units.TO_LITER.keys():
        return _humanize_volume(value, unit)
    else:
        return '{:.4f} {}'.format(value, markup_unit(unit))


def is_mass(unit):
    return units.is_mass(unit)


def basename(p):
    return path.basename(p)


def text_with_endmarker(text, marker='#'):
    lines = []
    for line in text.splitlines():
        if not line.strip() or line.strip() == marker:
            lines.append('<br>')
        else:
            lines.append(line)
    return markupsafe.Markup('<br>'.join(lines))
