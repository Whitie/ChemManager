# -*- coding: utf-8 -*-

import json

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.fields import JSONField
from core.models.chems import (
    validate_cas, validate_ecn, SIGNAL_WORD_CHOICES, STATE_CHOICES,
    WHC_CHOICES
)


class UploadedMSDS(models.Model):
    document = models.FileField(_('Document'), upload_to='uploaded_msds/%Y/')
    hash = models.CharField(max_length=64, editable=False, unique=True)
    added = models.DateTimeField(_('Added'), auto_now_add=True)
    added_by = models.ForeignKey(
        User, verbose_name=_('Added by'), related_name='uploads', blank=True,
        null=True, on_delete=models.SET_NULL)
    processed = models.BooleanField(_('Processed'), default=False)
    data = JSONField(_('Extracted Data'), blank=True, editable=False)
    name = models.CharField(_('Name'), max_length=200, blank=True)
    cas = models.CharField(
        _('CAS Registry Number'), max_length=12, blank=True,
        validators=[validate_cas]
    )
    token = models.CharField(_('Security token'), max_length=64,
                             editable=False)

    def __str__(self):
        return self.name or self.document.name

    def dump(self, filename):
        with open(filename, 'w', encoding='utf-8') as fp:
            json.dump(self.data, fp, sort_keys=True, indent=2)

    class Meta:
        verbose_name = _('Uploaded MSDS')
        verbose_name_plural = _("Uploaded MSDS's")
        ordering = ['-added']
        permissions = (
            ('upload', _('Can upload msds')),
        )


class ParsedData(models.Model):
    upload = models.ForeignKey(
        UploadedMSDS, verbose_name=_('Upload'), related_name='parsed',
        on_delete=models.CASCADE
    )
    name_en = models.CharField(_('Name (en)'), max_length=200, blank=True)
    producer = models.CharField(_('Producer'), max_length=200, blank=True)
    article_name = models.CharField(_('Article name'), max_length=200,
                                    blank=True)
    article_number = models.CharField(_('Article number'), max_length=64,
                                      blank=True)
    # DE: betrsichv
    security = models.CharField(_('Extra security'), max_length=100,
                                blank=True)
    # DE: AGW
    mac = models.DecimalField(
        _('MAC (mg/m3)'), max_digits=10, decimal_places=4,
        blank=True, null=True
    )
    # DE: BGW
    mabc = models.DecimalField(
        _('MABC (mg/L)'), max_digits=10, decimal_places=4, blank=True,
        null=True
    )
    # DE: Siedepunkt in °C
    boiling_low = models.DecimalField(
        _('Boiling Point low'), max_digits=5, decimal_places=1, blank=True,
        null=True, help_text=_('In °C.')
    )
    boiling_high = models.DecimalField(
        _('Boiling Point high'), max_digits=5, decimal_places=1, blank=True,
        null=True, help_text=_('In °C.')
    )
    # DE: Schüttdichte
    bulk_density = models.DecimalField(
        _('Bulk Density'), max_digits=10, decimal_places=4, blank=True,
        null=True, help_text=_('In kg/m3.')
    )
    cmr = models.BooleanField(_('CMR Substance'))
    # DE: Farbe
    color = models.CharField(_('Color'), max_length=30, blank=True)
    # DE: Dichte
    density = models.DecimalField(
        _('Density'), max_digits=10, decimal_places=4, blank=True,
        null=True, help_text=_('In g/cm3.')
    )
    density_temp = models.IntegerField(_('Density at Temperature'), blank=True,
                                       null=True, help_text=_('In °C.'))
    einecs = models.CharField(
        _('EC Number'), max_length=9, blank=True, validators=[validate_ecn]
    )
    euh = models.CharField(_('EUH'), max_length=100, blank=True,
                           help_text=_('Separate with ",".'))
    # DE: Geeignete Löschmittel
    ext_agents = models.TextField(blank=True)
    # DE: Nicht geeignete Löschmittel
    no_ext_agents = models.TextField(blank=True)
    # DE: Hinweise zur Brandbekämpfung
    fire_misc = models.TextField(blank=True)
    formula = models.CharField(_('Molecular Formula'), max_length=200,
                               blank=True)
    h = models.CharField(_('H'), max_length=200, blank=True,
                         help_text=_('Separate with ",".'))
    inchi = models.TextField(_('InChI'), blank=True)
    inchi_key = models.CharField(_('InChI-Key'), max_length=30, blank=True)
    # EU: Indicative Occupational Exposure Limit (mg/m3)
    ioelv = models.DecimalField(
        _('IOELV'), max_digits=10, decimal_places=4, blank=True, null=True,
        help_text=_('Indicative Occupational Exposure Limit (mg/m3)')
    )
    iupac_name = models.CharField(_('IUPAC Name'), max_length=200, blank=True)
    iupac_name_en = models.CharField(_('IUPAC Name (en)'), max_length=200,
                                     blank=True)
    # DE: Nummer zu Kennzeichnung der Gefahr (früher Kemler-Zahl)
    hin = models.CharField(_('HIN'), max_length=5, blank=True,
                           help_text=_('Hazard Identification Number'))
    storage_class = models.CharField(_('Storage class'), max_length=10,
                                     blank=True)
    # DE: Schmelzpunkt
    melting_low = models.DecimalField(
        _('Melting Point low'), max_digits=5, decimal_places=1, blank=True,
        null=True, help_text=_('In °C.')
    )
    melting_high = models.DecimalField(
        _('Melting Point high'), max_digits=5, decimal_places=1, blank=True,
        null=True, help_text=_('In °C.')
    )
    molar_mass = models.DecimalField(_('Molar Mass'), max_digits=12,
                                     decimal_places=4, blank=True, null=True)
    # DE: Geruch
    odor = models.CharField(_('Odor'), max_length=30, blank=True)
    p = models.CharField(_('P'), max_length=200, blank=True,
                         help_text=_('Separate with ",".'))
    pubchem_id = models.PositiveIntegerField(_('PubChem Compound ID'),
                                             blank=True, null=True)
    review_date = models.DateField(_('Last review'), blank=True, null=True)
    signal_word = models.CharField(_('Signal Word'), max_length=25, blank=True,
                                   choices=SIGNAL_WORD_CHOICES)
    smiles = models.TextField(_('SMILES'), blank=True)
    # DE: Löslichkeit in Wasser
    solubility_h2o = models.DecimalField(
        _('Solubility (H2O)'), max_digits=10, decimal_places=4, blank=True,
        null=True, help_text=_('In g/100g.')
    )
    solubility_h2o_temp = models.IntegerField(
        _('Solubility at Temperature'), blank=True, null=True,
        help_text=_('In °C.')
    )
    physical_state = models.CharField(_('Physical State'), max_length=1,
                                      choices=STATE_CHOICES, blank=True)
    structure = models.TextField(blank=True, editable=False)
    structure_fn = models.CharField(_('Filename'), max_length=200, blank=True)
    symbols = models.CharField(_('Symbols'), max_length=200, blank=True)
    synonyms = models.TextField(_('Synonyms'), blank=True,
                                help_text=_('Separate with ";".'))
    vwvws = models.IntegerField(_('DE: VWVWS'), blank=True, null=True)
    # DE: WGK
    whc = models.PositiveSmallIntegerField(
        _('WHC'), default=0, choices=WHC_CHOICES,
        help_text=_('Water Hazard Class')
    )

    def __str__(self):
        return self.upload.name

    class Meta:
        verbose_name = _('Parsed upload data')
        verbose_name_plural = _('Parsed upload data')
        ordering = ['name_en']
