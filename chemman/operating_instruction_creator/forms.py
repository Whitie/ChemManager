# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from core.utils import _get_users_by_permission
from core.models.chems import OperatingInstruction
from core.models.safety import GHSPictogram
from .models import (
    WorkDepartment, ProtectionPictogram
)

RELEASE_PERM = 'operating_instruction_creator.release'
EDIT_PERM = 'operating_instruction_creator.create'


class OIForm(forms.Form):
    msds_date = forms.DateField(label=_('MSDS Date'))
    dep_1 = forms.ModelChoiceField(
        label=_('Department 1'), queryset=WorkDepartment.objects.all()
    )
    dep_2 = forms.ModelChoiceField(
        label=_('Department 2'), queryset=WorkDepartment.objects.all(),
        required=False
    )
    signature = forms.ModelChoiceField(
        label=_('Signature'), queryset=User.objects.filter(
            **_get_users_by_permission(RELEASE_PERM, False))
    )
    pictograms = forms.ModelMultipleChoiceField(
        label=_('Pictograms'),
        queryset=GHSPictogram.objects.all().order_by('ref_num'),
        required=False
    )
    hazards = forms.CharField(
        label=_('Hazards for people and the environment'),
        widget=forms.Textarea
    )
    protection = forms.CharField(
        label=_('Protective measures and rules of conduct'),
        widget=forms.Textarea
    )
    protection_pics = forms.ModelMultipleChoiceField(
        label=_('Pictograms'), queryset=ProtectionPictogram.objects.all()
    )
    eye_protection = forms.CharField(label=_('Eye protection'), max_length=60)
    hand_protection = forms.CharField(
        label=_('Hand protection'), max_length=60
    )
    conduct = forms.CharField(
        label=_('Conduct in case of danger'), widget=forms.Textarea
    )
    green_cross = forms.BooleanField(
        label=_('Show green cross'), required=False
    )
    first_aid = forms.CharField(
        label=_('First aid'), widget=forms.Textarea
    )
    skin = forms.CharField(
        label=_('After skin contact'), max_length=150, required=False
    )
    eye = forms.CharField(
        label=_('After eye contact'), max_length=150, required=False
    )
    breathe = forms.CharField(
        label=_('After breathe in'), max_length=150, required=False
    )
    swallow = forms.CharField(
        label=_('After swallow'), max_length=150, required=False
    )
    disposal = forms.CharField(
        label=_('Proper disposal'), widget=forms.Textarea
    )
    ext_phone = forms.CharField(
        label=_('External help number'), max_length=20
    )
    int_phone = forms.CharField(
        label=_('Internal help number'), max_length=20
    )

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'uk-form-width-large'})


class ReleaseForm(forms.Form):
    substitutes = forms.ModelChoiceField(
        label=_('Substitutes'), queryset=OperatingInstruction.objects.all(),
        required=False, empty_label=_('Add new')
    )
    note = forms.CharField(
        label=_('Note'), widget=forms.Textarea, required=False
    )

    def __init__(self, *args, **kw):
        chem = kw.pop('chem')
        super().__init__(*args, **kw)
        self.fields['substitutes'].queryset = chem.operating_instructions.all()
