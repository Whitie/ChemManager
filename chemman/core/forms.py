# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from .models import (
    Company, Group, Storage, StoragePlace, StoredChemical, UNIT_CHOICES,
    CONTAINER_MATERIAL_CHOICES, QUALITY_CHOICES, COMPOSITION_CHOICES,
    MASS_CHOICES, StoredPackage, Order, Chemical, Department
)


FIELD_CHOICES = (
    ('hazard_statements__ref', _('H-Statement')),
    ('whc', _('WHC')),
    ('mac', _('MAC')),
    ('mabc', _('MABC')),
    ('molar_mass', _('Molar Mass')),
    ('storage_temperature', _('Storage Temperature')),
    ('pictograms__ref_num', _('Pictogram')),
    ('eu_hazard_statements__ref', _('EUH-Statement')),
    ('physical_data__melting_point_low', _('Melting Point')),
    ('physical_data__boiling_point_low', _('Boiling Point')),
)
EXPRESSION_CHOICES = (
    ('iexact', _('=')),
    ('icontains', _('\u2248')),
    ('gt', _('>')),
    ('gte', _('\u2265')),
    ('lt', _('<')),
    ('lte', _('\u2264')),
)
EXP_NUMBER_CHOICES = (
    ('exact', _('=')),
) + EXPRESSION_CHOICES[2:]
EXP_LOOKUP = dict(EXPRESSION_CHOICES)
EXP_LOOKUP['exact'] = _('=')
LINKAGE_CHOICES = (
    ('and', _('AND')),
    ('or', _('OR')),
)


def get_chemical(pk):
    pk = int(pk)
    if not pk:
        return None
    return Chemical.objects.select_related().get(pk=int(pk))


def get_chemicals():
    return [(0, '----')] + list(Chemical.objects.values_list('id', 'name'))


def _get_search_choices():
    return Chemical.objects.values_list('id', 'name')


class PlaceChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        dep = obj.storage.department or _('General')
        return '{}: {} -> {}'.format(dep, obj.storage.name, obj.name)


class ListGeneratorForm(forms.Form):
    name = forms.CharField(label=_('Name for this List'), required=False,
                           max_length=100)
    field_1 = forms.ChoiceField(choices=FIELD_CHOICES)
    exp_1 = forms.ChoiceField(choices=EXPRESSION_CHOICES)
    term_1 = forms.CharField()
    andor_2 = forms.ChoiceField(choices=LINKAGE_CHOICES, required=False)
    field_2 = forms.ChoiceField(choices=FIELD_CHOICES, required=False)
    exp_2 = forms.ChoiceField(choices=EXPRESSION_CHOICES, required=False)
    term_2 = forms.CharField(required=False)
    andor_3 = forms.ChoiceField(choices=LINKAGE_CHOICES, required=False)
    field_3 = forms.ChoiceField(choices=FIELD_CHOICES, required=False)
    exp_3 = forms.ChoiceField(choices=EXPRESSION_CHOICES, required=False)
    term_3 = forms.CharField(required=False)
    andor_4 = forms.ChoiceField(choices=LINKAGE_CHOICES, required=False)
    field_4 = forms.ChoiceField(choices=FIELD_CHOICES, required=False)
    exp_4 = forms.ChoiceField(choices=EXPRESSION_CHOICES, required=False)
    term_4 = forms.CharField(required=False)


class HandbookCommentForm(forms.Form):
    title = forms.CharField(
        label=_('Title'), required=False, widget=forms.TextInput(
            attrs={'placeholder': _('Title (optional)')}
        )
    )
    text = forms.CharField(
        label=_('Text'), widget=forms.Textarea(
            attrs={'placeholder': _('Write your comment')}
        )
    )


class NewChapterForm(forms.Form):
    title = forms.CharField(label=_('Title'), max_length=100)
    number = forms.IntegerField(label=_('Number'))
    synopsis = forms.CharField(label=_('Synopsis'), widget=forms.Textarea,
                               required=False)


class NewParagraphForm(forms.Form):
    title = forms.CharField(label=_('Title'), max_length=100)
    number = forms.IntegerField(label=_('Number'))


class NewPackageForm(forms.Form):
    company = forms.ModelChoiceField(
        label=_('Supplier'), queryset=Company.objects.all(), required=False
    )
    msds = forms.FileField(label=_('MSDS'), required=False)
    published = forms.DateField(
        label=_('MSDS publishing date'), required=False,
        input_formats=['%Y-%m-%d', '%y-%m-%d', '%d.%m.%Y', '%d.%m.%y']
    )
    quality = forms.ChoiceField(label=_('Quality'), choices=QUALITY_CHOICES)
    name_extra = forms.CharField(
        label=_('Name extra'), required=False, max_length=100,
        help_text=_('E. g. supplier specific name or label.')
    )
    storage = forms.ModelChoiceField(
        label=_('Target Storage'), queryset=Storage.objects.all()
    )

    def __init__(self, chemical, *args, **kw):
        super(NewPackageForm, self).__init__(*args, **kw)
        msds_choices = [(0, _('--------'))]
        for stchem in StoredChemical.objects.filter(chemical=chemical):
            if stchem.msds:
                text = '{}, {}'.format(stchem.get_quality_display(),
                                       stchem.company)
                msds_choices.append((stchem.msds.id, text))
        self.fields['old_msds'] = forms.TypedChoiceField(
            label=_('Or choose present'), choices=msds_choices,
            coerce=int, empty_value=None, required=False
        )


class NewNormalPackageForm(forms.Form):
    content = forms.DecimalField(label=_('Content'), max_digits=7,
                                 decimal_places=2)
    unit = forms.ChoiceField(label=_('Unit'), choices=UNIT_CHOICES)
    composition = forms.ChoiceField(label=_('Composition'),
                                    choices=COMPOSITION_CHOICES)
    container_material = forms.ChoiceField(
        label=_('Container Material'), choices=CONTAINER_MATERIAL_CHOICES
    )
    supplier_ident = forms.CharField(label=_('Article No.'), max_length=20,
                                     required=False)
    supplier_code = forms.CharField(label=_('Code'), max_length=100,
                                    required=False)
    supplier_batch = forms.CharField(label=_('Batch No.'), max_length=30,
                                     required=False)
    best_before = forms.DateField(
        label=_('Best before'), required=False,
        input_formats=['%Y-%m-%d', '%y-%m-%d', '%d.%m.%Y', '%d.%m.%y']
    )

    def __init__(self, storage, *args, **kw):
        super(NewNormalPackageForm, self).__init__(*args, **kw)
        self.fields['place'] = forms.ModelChoiceField(
            label=_('Storage Place'),
            queryset=StoragePlace.objects.filter(storage=storage)
        )


class NewSpecialPackageForm(NewNormalPackageForm):
    brutto_mass = forms.DecimalField(label=_('Brutto Mass'), max_digits=7,
                                     decimal_places=2)
    brutto_mass_unit = forms.ChoiceField(label=_('Unit'),
                                         choices=MASS_CHOICES)


class DisposeForm(forms.Form):
    reason = forms.CharField(label=_('Reason'), max_length=100)


class ProfileForm(forms.Form):
    first_name = forms.CharField(label=_('First Name'), max_length=30)
    last_name = forms.CharField(label=_('Last Name'), max_length=30)
    internal_phone = forms.CharField(label=_('Internal Phone'), max_length=30,
                                     required=False)


class ConsumeSpecialForm(forms.Form):
    mass_after = forms.DecimalField(label=_('Mass after'), max_digits=8,
                                    decimal_places=4)
    mass_after_unit = forms.ChoiceField(label=_('Unit'), choices=MASS_CHOICES)
    used_by = forms.ModelChoiceField(
        label=_('Instructor'),
        queryset=User.objects.all().order_by('last_name')
    )
    group = forms.ModelChoiceField(
        label=_('Group'),
        queryset=Group.objects.all().order_by('name')
    )
    task = forms.CharField(label=_('Task'), widget=forms.Textarea)


class ConsumeNormalForm(forms.Form):
    removed_quantity = forms.DecimalField(
        label=_('Removed quantity'), max_digits=8, decimal_places=4
    )
    removed_quantity_unit = forms.ChoiceField(
        label=_('Unit'), choices=[]
    )
    group = forms.ModelChoiceField(
        label=_('Group'), required=False,
        queryset=Group.objects.all().order_by('name')
    )
    task = forms.CharField(label=_('Task'), widget=forms.Textarea,
                           required=False)


class InventoryJSONForm(forms.Form):
    package = forms.ModelChoiceField(queryset=StoredPackage.objects.all())
    value = forms.DecimalField(max_digits=9, decimal_places=4, required=False)
    unit = forms.CharField(max_length=2)
    old_value = forms.DecimalField(max_digits=9, decimal_places=4)
    old_unit = forms.CharField(max_length=2)
    note = forms.CharField(max_length=250, required=False)
    ok = forms.BooleanField(required=False)
    special_log = forms.BooleanField(required=False)


class DeliverOrderForm(forms.Form):
    place = forms.ModelChoiceField(
        queryset=StoragePlace.objects.all()
    )
    order = forms.ModelChoiceField(queryset=Order.objects.all())
    delivered = forms.IntegerField()


class DeliverJSONForm(forms.Form):
    package = forms.ModelChoiceField(queryset=StoredPackage.objects.all())
    composition = forms.ChoiceField(choices=COMPOSITION_CHOICES)
    container = forms.ChoiceField(choices=CONTAINER_MATERIAL_CHOICES)
    batch = forms.CharField(required=False)
    best_before = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d', '%y-%m-%d', '%d.%m.%Y', '%d.%m.%y']
    )
    brutto = forms.DecimalField(max_digits=7, decimal_places=2, required=False)
    brutto_unit = forms.ChoiceField(choices=MASS_CHOICES, required=False)


class ToxActionForm(forms.Form):
    group = forms.ModelChoiceField(
        label=_('Group'), queryset=Group.objects.filter(active=True),
        required=False
    )
    instructor = forms.ModelChoiceField(
        label=_('Instructor'), queryset=User.objects.filter(is_active=True),
        required=False
    )
    from_date = forms.DateField(
        label=_('From Date'), input_formats=['%d.%m.%Y']
    )
    to_date = forms.DateField(
        label=_('To Date'), input_formats=['%d.%m.%Y']
    )
    only_tox = forms.BooleanField(label=_('Show only toxic'), required=False)


class InitialDeliveryForm(forms.Form):
    chemical = forms.TypedChoiceField(
        coerce=get_chemical, choices=get_chemicals, empty_value=0,
        required=False, label=_('Chemical')
    )
    quality = forms.ChoiceField(choices=QUALITY_CHOICES, label=_('Quality'))
    name_extra = forms.CharField(
        required=False, max_length=100, label=_('Name extra'),
        help_text=_('E. g. supplier specific name or label.')
    )
    place = PlaceChoiceField(
        label=_('Place'),
        queryset=StoragePlace.objects.select_related().all(
            ).order_by('storage__department__name', 'storage__name', 'name')
    )
    content = forms.DecimalField(max_digits=7, decimal_places=2,
                                 label=_('Content'))
    unit = forms.ChoiceField(choices=UNIT_CHOICES, label=_('Unit'))
    composition = forms.ChoiceField(choices=COMPOSITION_CHOICES,
                                    label=_('Composition'))
    container_material = forms.ChoiceField(
        choices=CONTAINER_MATERIAL_CHOICES, required=False,
        label=_('Container Material')
    )
    delivered_for = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).exclude(
            username__icontains='admin'
        ).order_by('username'),
        required=False, label=_('Delivered for')
    )
    best_before = forms.DateField(
        required=False, label=_('Best before'),
        input_formats=['%Y-%m-%d', '%y-%m-%d', '%d.%m.%Y', '%d.%m.%y']
    )
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(), required=False, label=_('Company')
    )
    msds = forms.FileField(
        label=_('MSDS'),
        required=False, help_text=_('Leave empty, to get the one from '
                                    'the choosen chemical.')
    )
    published = forms.DateField(
        required=False, label=_('Published'),
        input_formats=['%Y-%m-%d', '%y-%m-%d', '%d.%m.%Y', '%d.%m.%y']
    )
    supplier_ident = forms.CharField(max_length=20, required=False,
                                     label=_('Supplier ID'))
    supplier_code = forms.CharField(max_length=100, required=False,
                                    label=_('Supplier CODE'))
    supplier_batch = forms.CharField(max_length=30, required=False,
                                     label=_('Supplier BATCH'))
    brutto_mass = forms.DecimalField(max_digits=7, decimal_places=2,
                                     required=False, label=_('Brutto mass'))
    brutto_mass_unit = forms.ChoiceField(choices=MASS_CHOICES,
                                         required=False, label=_('Unit'))

    def __init__(self, *args, **kw):
        super(InitialDeliveryForm, self).__init__(*args, **kw)
        for n, f in self.fields.items():
            f.widget.attrs.update({'class': 'uk-form-small'})
        f = self.fields
        f['chemical'].widget.attrs.update({'class': 'uk-form-small chem'})
        f['published'].widget.attrs.update({'class': 'uk-form-small dt'})
        f['best_before'].widget.attrs.update({'class': 'uk-form-small dt'})


class SearchChemicalForm(forms.Form):
    pass


class SearchPackageForm(forms.Form):
    chemical = forms.TypedChoiceField(
        label=_('Chemical'), coerce=get_chemical,
        choices=_get_search_choices
    )
    storage = forms.ModelChoiceField(
        label=_('Storage'), required=False, queryset=Storage.objects.all()
    )
    department = forms.ModelChoiceField(
        label=_('Department'), required=False,
        queryset=Department.objects.all()
    )
    exp = forms.ChoiceField(choices=EXP_NUMBER_CHOICES)
    content = forms.DecimalField(
        label=_('Content'), max_digits=7, decimal_places=2, required=False
    )
    unit = forms.ChoiceField(choices=UNIT_CHOICES, initial='g')
    composition = forms.ChoiceField(
        label=_('Composition'), required=False,
        choices=(('', _('--------')),) + COMPOSITION_CHOICES
    )
    container_material = forms.ChoiceField(
        label=_('Container Material'), required=False,
        choices=(('', _('--------')),) + CONTAINER_MATERIAL_CHOICES
    )
