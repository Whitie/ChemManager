# -*- coding: utf-8 -*-

import requests

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from .. import utils
from .base import Department
from .safety import (GHSPictogram, HazardStatement, EUHazardStatement,
                     PrecautionaryStatement, StorageClass)


URLS = {
    'cas': 'http://www.commonchemistry.org/ChemicalDetail.aspx?ref={}',
    'pubchem_id': 'http://pubchem.ncbi.nlm.nih.gov/compound/{}',
    'drugbank': 'http://www.drugbank.ca/drugs/{}',
    'kegg': 'http://www.kegg.jp/entry/{}',
}
STATE_CHOICES = (
    ('s', _('solid')),
    ('l', _('liquid')),
    ('g', _('gaseous')),
)
TEMPERATURE_CHOICES = (
    ('super_frosted', _('super frosted (-80°C)')),
    ('frosted', _('frosted (-18°C)')),
    ('cold', _('cold (4°C)')),
    ('normal', _('normal (15 - 25°C)')),
    ('special', _('special (give temp. in properties)')),
)
SIGNAL_WORD_CHOICES = (
    ('', '-'),
    ('danger', _('Danger')),  # Gefahr
    ('warning', _('Warning')),  # Achtung
)
WHC_CHOICES = (
    (0, _('0 - Non-hazardous to water')),
    (1, _('1 - Low hazard to waters')),
    (2, _('2 - Hazard to waters')),
    (3, _('3 - Severe hazard to waters')),
)
SAFETY_LIMIT_UNITS = (
    ('mg/m3', _('mg/m3')),
    ('mg/L', _('mg/L')),
    ('mL/m3', _('mL/m3')),
)


def validate_cas(val):
    if val.strip() and not utils.validate_cas(val):
        raise ValidationError(
            _('%(value)s is not a valid CAS number'),
            params={'value': val}
        )


def validate_ecn(val):
    if val.strip() and not utils.validate_ecn(val):
        raise ValidationError(
            _('%(value)s is not a valid EC number'),
            params={'value': val}
        )


class Chemical(models.Model):
    name = models.CharField(_('Name'), max_length=200)
    name_en = models.CharField(_('Name (en)'), max_length=200, blank=True)
    slug = models.SlugField(_('Slug'), max_length=200, unique=True)
    iupac_name = models.CharField(_('IUPAC Name'), max_length=200, blank=True)
    iupac_name_en = models.CharField(_('IUPAC Name (en)'), max_length=200,
                                     blank=True)
    structure = models.FileField(_('Structure'), blank=True,
                                 upload_to=utils.structure_path)
    formula = models.CharField(_('Molecular Formula'), max_length=200,
                               blank=True)
    molar_mass = models.DecimalField(_('Molar Mass'), max_digits=12,
                                     decimal_places=4, blank=True, null=True)
    flammable = models.BooleanField(_('Flammable'), default=False)
    storage_temperature = models.CharField(
        _('Storage Temperature'), choices=TEMPERATURE_CHOICES,
        default='normal', max_length=15
    )
    storage_temperature_special = models.IntegerField(
        _('Special Temperature'), blank=True, null=True,
        help_text=_('Only give a temperature here if you have selected '
                    '"special" on Storage Temperature field.')
    )
    signal_word = models.CharField(_('Signal Word'), max_length=25, blank=True,
                                   choices=SIGNAL_WORD_CHOICES)
    pictograms = models.ManyToManyField(
        GHSPictogram, verbose_name=_('GHS Pictograms'), blank=True,
        related_name='chemicals'
    )
    hazard_statements = models.ManyToManyField(
        HazardStatement, verbose_name=_('Hazard Statements'), blank=True,
        related_name='chemicals',
    )
    eu_hazard_statements = models.ManyToManyField(
        EUHazardStatement, verbose_name=_('EU Hazard Statements'), blank=True,
        related_name='chemicals',
    )
    precautionary_statements = models.ManyToManyField(
        PrecautionaryStatement, verbose_name=_('Precautionary Statements'),
        related_name='chemicals', blank=True,
    )
    # DE: WGK
    whc = models.PositiveSmallIntegerField(
        _('WHC'), default=0, choices=WHC_CHOICES,
        help_text=_('Water Hazard Class')
    )
    # DE: AGW
    mac = models.DecimalField(
        _('MAC'), max_digits=10, decimal_places=4, blank=True, null=True,
        help_text=_('Maximum Allowable Concentration')
    )
    mac_unit = models.CharField(_('MAC Unit'), max_length=5, blank=True,
                                choices=SAFETY_LIMIT_UNITS)
    # DE: BGW
    mabc = models.DecimalField(
        _('MABC'), max_digits=10, decimal_places=4, blank=True, null=True,
        help_text=_('Maximum Allowable Biological Concentration')
    )
    mabc_unit = models.CharField(_('MABC Unit'), max_length=5, blank=True,
                                 choices=SAFETY_LIMIT_UNITS)
    # DE: MAK
    mac_old = models.DecimalField(
        _('MAC (old)'), max_digits=10, decimal_places=4, blank=True, null=True,
        help_text=_('Maximum Allowable Concentration (old)')
    )
    mac_old_unit = models.CharField(_('MAC (old) Unit'), max_length=5,
                                    blank=True, choices=SAFETY_LIMIT_UNITS)
    # DE: LGK
    storage_class = models.ForeignKey(
        StorageClass, verbose_name=_('Storage Class'), blank=True, null=True,
        related_name='chemicals', on_delete=models.SET_NULL
    )
    # EU: Binding Occupational Exposure Limit (mg/m3)
    boelv = models.DecimalField(
        _('BOELV'), max_digits=10, decimal_places=4, blank=True, null=True,
        help_text=_('Binding Occupational Exposure Limit (mg/m3)')
    )
    # EU: Indicative Occupational Exposure Limit (mg/m3)
    ioelv = models.DecimalField(
        _('IOELV'), max_digits=10, decimal_places=4, blank=True, null=True,
        help_text=_('Indicative Occupational Exposure Limit (mg/m3)')
    )
    # DE: Nummer zu Kennzeichnung der Gefahr
    hin = models.CharField(_('HIN'), max_length=5, blank=True,
                           help_text=_('Hazard Identification Number'))
    ext_media = models.TextField(_('Extinguishing Media'), blank=True)
    un_ext_media = models.TextField(_('Unsuitable Extinguishing Media'),
                                    blank=True)
    fire_advice = models.TextField(_('Fire Advice'), blank=True)
    wiki_link = models.CharField(_('Wikipedia Link'), max_length=300,
                                 blank=True)
    special_log = models.BooleanField(
        _('Special Log'), default=False,
        help_text=_('Set this if you need detailed information about usage of '
                    'this substance.')
    )
    cmr = models.BooleanField(_('CMR Substance'), default=False)
    active = models.BooleanField(
        _('Active'), default=True, help_text=_('Only active chemicals are '
                                               'displayed in lists.')
    )
    added = models.DateTimeField(_('Added'), auto_now_add=True)
    added_by = models.ForeignKey(
        User, verbose_name=_('Added by'), blank=True, null=True,
        editable=False, on_delete=models.SET_NULL
    )
    last_updated = models.DateTimeField(_('Last Updated'), auto_now=True)

    def __str__(self):
        if hasattr(self, 'identifiers'):
            cas = self.identifiers.cas or '-'
        else:
            cas = '-'
        return '{}, CAS: {}'.format(self.display_name, cas)

    @property
    def display_name(self):
        return self.name or self.name_en or self.iupac_name

    @property
    def acutely_toxic(self):
        for pic in self.pictograms.all():
            if pic.ref_num == 6:
                return True
        return False

    @property
    def sc_info_url(self):
        if self.storage_class and getattr(self.identifiers, 'cas', None):
            return ('http://www.zusammenlagerung.de/info.php?submit2=search&'
                    'info_name={cas}&submit=search'.format(
                        cas=self.identifiers.cas))
        return '#'

    @property
    def has_oi(self):
        return bool(self.operating_instructions.all().count())

    def update_wiki_link(self):
        url = settings.WIKI_LINK.format(name=self.name)
        r = requests.get(url)
        if r.status_code != 404:
            self.wiki_link = url
        else:
            self.wiki_link = settings.WIKI_SEARCH_LINK.format(name=self.name)

    class Meta:
        verbose_name = _('Chemical')
        verbose_name_plural = _('Chemicals')
        ordering = ['name']
        permissions = (
            ('manage', _('Can manage chemicals')),
        )


class Identifiers(models.Model):
    chemical = models.OneToOneField(
        Chemical, verbose_name=_('Chemical'), related_name='identifiers',
        on_delete=models.CASCADE
    )
    cas = models.CharField(
        _('CAS Registry Number'), max_length=12, blank=True,
        help_text=_('CAS = Chemical Abstract Service'),
        validators=[validate_cas]
    )
    un = models.PositiveIntegerField(_('UN Number'), blank=True, null=True)
    einecs = models.CharField(
        _('EC Number'), max_length=9, blank=True,
        help_text=_('European Community Number (EC No., EINECS No., EC#)'),
        validators=[validate_ecn]
    )
    inchi = models.TextField(_('InChI'), blank=True, help_text=_('InChI = '
                             'International Chemical Identifier'))
    inchi_key = models.CharField(_('InChI-Key'), max_length=30, blank=True)
    smiles = models.TextField(
        _('SMILES'), blank=True,
        help_text=_('SMILES = Simplified Molecular Input Line Entry '
                    'Specification')
    )
    pubchem_id = models.PositiveIntegerField(_('PubChem Compound ID'),
                                             blank=True, null=True)
    drugbank = models.CharField(_('DrugBank'), max_length=15, blank=True)
    kegg = models.CharField(_('KEGG Number'), max_length=15, blank=True,
                            help_text=_('KEGG = Kyoto Encyclopedia of '
                                        'Genes and Genomes'))
    imported_from = models.FileField(_('Imported from'), upload_to='msds/ref',
                                     blank=True)

    def __str__(self):
        return self.cas

    class Meta:
        verbose_name = _('Identifiers')
        verbose_name_plural = _('Identifiers')

    def url_for(self, which):
        which = which.lower()
        try:
            return URLS[which].format(getattr(self, which))
        except (KeyError, AttributeError):
            return ''


class PhysicalData(models.Model):
    chemical = models.OneToOneField(
        Chemical, verbose_name=_('Chemical'), related_name='physical_data',
        on_delete=models.CASCADE
    )
    physical_state = models.CharField(_('Physical State'), max_length=1,
                                      choices=STATE_CHOICES, blank=True)
    # DE: Farbe
    color = models.CharField(_('Color'), max_length=30, blank=True)
    # DE: Geruch
    odor = models.CharField(_('Odor'), max_length=30, blank=True)
    # DE: Dichte
    density = models.DecimalField(
        _('Density'), max_digits=10, decimal_places=4, blank=True,
        null=True, help_text=_('In g/cm3.')
    )
    density_temp = models.IntegerField(_('Density at Temperature'), blank=True,
                                       null=True, help_text=_('In °C.'))
    # DE: Schüttdichte
    bulk_density = models.DecimalField(
        _('Bulk Density'), max_digits=10, decimal_places=4, blank=True,
        null=True, help_text=_('In kg/m3.')
    )
    # DE: Schmelzpunkt
    melting_point_low = models.DecimalField(
        _('Melting Point low'), max_digits=5, decimal_places=1, blank=True,
        null=True, help_text=_('If this chemical has a defined melting point '
                               'use only this field. Give in °C.')
    )
    melting_point_high = models.DecimalField(
        _('Melting Point high'), max_digits=5, decimal_places=1, blank=True,
        null=True, help_text=_('In °C.')
    )
    # DE: Siedepunkt
    boiling_point_low = models.DecimalField(
        _('Boiling Point low'), max_digits=5, decimal_places=1, blank=True,
        null=True, help_text=_('If this chemical has a defined boiling point '
                               'use only this field. Give in °C.')
    )
    boiling_point_high = models.DecimalField(
        _('Boiling Point high'), max_digits=5, decimal_places=1, blank=True,
        null=True, help_text=_('In °C.')
    )
    # DE: Löslichkeit in Wasser
    solubility_h2o = models.DecimalField(
        _('Solubility (H2O)'), max_digits=10, decimal_places=4, blank=True,
        null=True, help_text=_('In g/100g.')
    )
    solubility_h2o_temp = models.IntegerField(
        _('Solubility at Temperature'), blank=True, null=True,
        help_text=_('In °C.')
    )

    def __str__(self):
        return self.chemical.display_name

    def _format_range(self, low, high, unit):
        if not low:
            return '-'
        if not high:
            return '{}{}'.format(high, unit)
        else:
            return '{} - {}{}'.format(low, high, unit)

    @property
    def boiling_point(self):
        return self._format_range(self.boiling_point_low,
                                  self.boiling_point_high, '°C')

    @property
    def melting_point(self):
        return self._format_range(self.melting_point_low,
                                  self.melting_point_high, '°C')

    class Meta:
        verbose_name = _('Physical Data')
        verbose_name_plural = _('Physical Data')
        ordering = ['chemical__name']


class Synonym(models.Model):
    chemical = models.ForeignKey(
        Chemical, verbose_name=_('Chemical'), related_name='synonyms',
        on_delete=models.CASCADE
    )
    name = models.CharField(_('Name'), max_length=200)

    def __str__(self):
        return '{} -> {}'.format(self.name, self.chemical.display_name)

    class Meta:
        verbose_name = _('Synonym')
        verbose_name_plural = _('Synonyms')
        ordering = ['chemical__name', 'name']


class DisposalInstructions(models.Model):
    chemical = models.ForeignKey(
        Chemical, verbose_name=_('Chemical'),
        related_name='disposal_instructions', on_delete=models.CASCADE
    )
    method = models.CharField(_('Method'), max_length=50)

    def __str__(self):
        self.chemical.display_name


class OperatingInstruction(models.Model):
    chemical = models.ForeignKey(
        Chemical, verbose_name=_('Chemical'),
        related_name='operating_instructions', on_delete=models.CASCADE
    )
    department = models.ForeignKey(
        Department, verbose_name=_('Department'),
        related_name='operating_instructions', on_delete=models.CASCADE
    )
    notes = models.TextField(_('Notes'), blank=True)
    document = models.FileField(
        _('Document'), upload_to='operating_instructions/%Y'
    )
    added = models.DateField(auto_now_add=True)
    last_updated = models.DateField(auto_now=True)
    last_updated_by = models.ForeignKey(
        User, verbose_name=_('Last updated by'), blank=True, null=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return '{} -> {}'.format(self.chemical.display_name,
                                 self.department.name)

    class Meta:
        verbose_name = _('Operating Instruction')
        verbose_name_plural = _('Operating Instructions')
        ordering = ['department__name', 'chemical__name']
