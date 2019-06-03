# -*- coding: utf-8 -*-

from decimal import Decimal as D

from django.conf import settings


D_3 = D(10**3)
D_6 = D(10**6)
D_9 = D(10**9)

TO_GRAMM = {
    'ng': lambda x: x / D_9,
    'µg': lambda x: x / D_6,
    'mg': lambda x: x / D_3,
    'g': lambda x: x,
    'kg': lambda x: x * D_3,
    't': lambda x: x * D_6,
}
GRAMM_TO_UNIT = {
    'ng': lambda x: x * D_9,
    'µg': lambda x: x * D_6,
    'mg': lambda x: x * D_3,
    'g': lambda x: x,
    'kg': lambda x: x / D_3,
    't': lambda x: x / D_6
}
TO_LITER = {
    'µl': lambda x: x / D_6,
    'ml': lambda x: x / D_3,
    'l': lambda x: x,
    'm3': lambda x: x * D_3,
}
LITER_TO_UNIT = {
    'µl': lambda x: x * D_6,
    'ml': lambda x: x * D_3,
    'l': lambda x: x,
    'm3': lambda x: x / D_3,
}


def _convert_mass(value, from_unit, to_unit):
    value_in_gramm = TO_GRAMM[from_unit](value)
    return GRAMM_TO_UNIT[to_unit](value_in_gramm)


def _convert_volume(value, from_unit, to_unit):
    value_in_liter = TO_LITER[from_unit](value)
    return LITER_TO_UNIT[to_unit](value_in_liter)


def convert(value, from_unit, to_unit=None):
    if from_unit.lower() in TO_GRAMM.keys():
        if to_unit is None:
            to_unit = settings.DEFAULT_MASS_UNIT
        return _convert_mass(value, from_unit.lower(), to_unit.lower())
    else:
        if to_unit is None:
            to_unit = settings.DEFAULT_VOLUME_UNIT
        return _convert_volume(value, from_unit.lower(), to_unit.lower())


def is_mass(unit):
    return unit.lower() in TO_GRAMM.keys()


def get_default(value, unit):
    if is_mass(unit):
        to_unit = settings.DEFAULT_MASS_UNIT
    else:
        to_unit = settings.DEFAULT_VOLUME_UNIT
    return convert(value, unit, to_unit), to_unit


def make_unit(value, unit):
    if is_mass(unit):
        return Mass(value, unit)
    else:
        return Volume(value, unit)


def volume_to_mass(value, unit, chemical):
    value_in_ml = convert(value, unit, 'ml')
    if not chemical.physical_data.density:
        density = D(1)
    else:
        density = chemical.physical_data.density
    return value_in_ml * density


def mass_to_volume(value, unit, chemical):
    value_in_gramm = convert(value, unit, 'g')
    if not chemical.physical_data.density:
        density = D(1)
    else:
        density = chemical.physical_data.density
    return value_in_gramm / density


class Mass:

    error_message = 'Unit must be one of [{}], NOT {}'
    valid_units = set(TO_GRAMM.keys())

    def __init__(self, value, unit):
        if unit.lower() not in self.valid_units:
            raise ValueError(
                self.error_message.format(', '.join(self.valid_units), unit)
            )
        if not isinstance(value, D):
            value = D(str(value))
        self.value = value
        self.unit = unit

    def __str__(self):
        return '{:.4f} {}'.format(self.value, self.unit)

    def __repr__(self):
        return '<Mass({!r}, "{}")>'.format(self.value, self.unit)

    @property
    def value_in_gramm(self):
        return convert(self.value, self.unit, 'g')

    def convert(self, to_unit):
        if to_unit.lower() not in self.valid_units:
            raise ValueError(
                self.error_message.format(', '.join(self.valid_units), to_unit)
            )
        v = convert(self.value, self.unit, to_unit)
        return Mass(v, to_unit)

    def __nonzero__(self):
        if self < Mass(0.1, 'µg'):
            return False
        return bool(self.value)

    def __eq__(self, other):
        return self.value_in_gramm == other.value_in_gramm

    def __ne__(self, other):
        return self.value_in_gramm != other.value_in_gramm

    def __lt__(self, other):
        return self.value_in_gramm < other.value_in_gramm

    def __gt__(self, other):
        return self.value_in_gramm > other.value_in_gramm

    def __le__(self, other):
        return self.value_in_gramm <= other.value_in_gramm

    def __ge__(self, other):
        return self.value_in_gramm >= other.value_in_gramm

    def __add__(self, other):
        in_gramm = self.value_in_gramm + other.value_in_gramm
        return Mass(convert(in_gramm, 'g', self.unit), self.unit)

    def __sub__(self, other):
        in_gramm = self.value_in_gramm - other.value_in_gramm
        return Mass(convert(in_gramm, 'g', self.unit), self.unit)

    def __abs__(self):
        return Mass(abs(self.value), self.unit)

    def comp(self, other):
        return is_mass(other.unit)


class Volume:

    error_message = 'Unit must be one of [{}], NOT {}'
    valid_units = set(TO_LITER.keys())

    def __init__(self, value, unit):
        if unit.lower() not in self.valid_units:
            raise ValueError(
                self.error_message.format(', '.join(self.valid_units), unit)
            )
        if not isinstance(value, D):
            value = D(str(value))
        self.value = value
        self.unit = unit

    def __str__(self):
        return '{:.4f} {}'.format(self.value, self.unit)

    def __repr__(self):
        return '<Volume({!r}, "{}")>'.format(self.value, self.unit)

    @property
    def value_in_liter(self):
        return convert(self.value, self.unit, 'L')

    def convert(self, to_unit):
        if to_unit.lower() not in self.valid_units:
            raise ValueError(
                self.error_message.format(', '.join(self.valid_units), to_unit)
            )
        v = convert(self.value, self.unit, to_unit)
        return Volume(v, to_unit)

    def __nonzero__(self):
        if self < Volume(1, 'µL'):
            return False
        return bool(self.value)

    def __eq__(self, other):
        return self.value_in_liter == other.value_in_liter

    def __ne__(self, other):
        return self.value_in_liter != other.value_in_liter

    def __lt__(self, other):
        return self.value_in_liter < other.value_in_liter

    def __gt__(self, other):
        return self.value_in_liter > other.value_in_liter

    def __le__(self, other):
        return self.value_in_liter <= other.value_in_liter

    def __ge__(self, other):
        return self.value_in_liter >= other.value_in_liter

    def __add__(self, other):
        in_liter = self.value_in_liter + other.value_in_liter
        return Volume(convert(in_liter, 'L', self.unit), self.unit)

    def __sub__(self, other):
        in_liter = self.value_in_liter - other.value_in_liter
        return Volume(convert(in_liter, 'L', self.unit), self.unit)

    def __abs__(self):
        return Volume(abs(self.value), self.unit)

    def comp(self, other):
        return not is_mass(other.unit)
