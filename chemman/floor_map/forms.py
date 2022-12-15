# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _

from core.models.storage import Building


def get_highest_level(building):
    return max(building.floors.values_list('level', flat=True))


def get_highest_level_all():
    buildings = Building.objects.all()
    levels = []
    for building in buildings:
        levels.append(get_highest_level(building))
    return max(levels)


def get_level_choices():
    return [(x, str(x)) for x in range(get_highest_level_all() + 1)]


class ViewFloorForm(forms.Form):
    building = forms.ModelChoiceField(
        label=_('Building'), queryset=Building.objects.all().order_by('name'),
        empty_label=None
    )
    level = forms.TypedChoiceField(
        label=_('Level'), coerce=int, choices=get_level_choices
    )
