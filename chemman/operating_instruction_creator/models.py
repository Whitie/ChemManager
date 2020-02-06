# -*- coding: utf-8 -*-

"""
German description:
-------------------

Betriebsanweisung für Gefahrstoffe
Nach § 14 Gefahrstoffverordnung (GefStoffV) hat der Unternehmer den Umgang mit
Gefahrstoffen (gefährliche Stoffe) in Betriebsanweisungen schriftlich zu
regeln. Inhaltliche Gestaltung und Aufbau sind in der TRGS 555 geregelt.

Betriebsanweisungen sind gem. TRGS 555 in folgende Bereiche gegliedert:

1. Arbeitsbereiche, Arbeitsplatz, Tätigkeit,
2. Gefahrstoffe (Bezeichnung),
3. Gefahren für Mensch und Umwelt,
4. Schutzmaßnahmen, Verhaltensregeln,
5. Verhalten im Gefahrfall,
6. Erste Hilfe und
7. Sachgerechte Entsorgung.
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models.chems import Chemical


def get_sentinel_user():
    return User.objects.get_or_create(username='deleted')[0]


class WorkDepartment(models.Model):
    name = models.CharField(_('Name'), max_length=25)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Work Department')
        verbose_name_plural = _('Work Departments')
        ordering = ['name']


class ProtectionPictogram(models.Model):
    ident = models.CharField(_('Identifier'), max_length=10)
    icon = models.FileField(upload_to='oic')
    description = models.CharField(_('Description'), max_length=30,
                                   blank=True)

    def __str__(self):
        return f'{self.ident} - {self.description}'

    class Meta:
        verbose_name = _('Protection Pictogram')
        verbose_name_plural = _('Protection Pictograms')
        ordering = ['ident']


class FirstAidPictogram(models.Model):
    ident = models.CharField(_('Identifier'), max_length=10)
    icon = models.FileField(upload_to='oic')
    description = models.CharField(_('Description'), max_length=30,
                                   blank=True)

    def __str__(self):
        return f'{self.ident} - {self.description}'

    class Meta:
        verbose_name = _('First Aid Pictogram')
        verbose_name_plural = _('First Aid Pictograms')
        ordering = ['ident']


class OperatingInstructionDraft(models.Model):
    chemical = models.ForeignKey(
        Chemical, verbose_name=_('Chemical'), on_delete=models.CASCADE,
        related_name='operating_instruction_drafts'
    )
    work_departments = models.ManyToManyField(
        WorkDepartment, verbose_name=_('Work Departments'),
        related_name='operating_instruction_drafts'
    )
    responsible = models.ForeignKey(
        User, verbose_name=_('Responsible'), related_name='drafts',
        on_delete=models.SET(get_sentinel_user)
    )
    signature = models.ForeignKey(
        User, verbose_name=_('Signature'), related_name='sig_drafts',
        on_delete=models.SET(get_sentinel_user)
    )
    hazards = models.TextField(
        _('Hazards for people and the environment'), default='-'
    )
    protection = models.TextField(
        _('Protective measures and rules of conduct'), default='-'
    )
    protection_pics = models.ManyToManyField(
        ProtectionPictogram, verbose_name=_('Protection Pictograms')
    )
    eye_protection = models.CharField(_('Eye protection'), max_length=60)
    hand_protection = models.CharField(_('Hand protection'), max_length=60)
    conduct = models.TextField(
        _('Conduct in case of danger'), default='-'
    )
    green_cross = models.BooleanField(_('Green Cross'), default=True)
    first_aid = models.TextField(_('First aid'), default='-')
    skin = models.CharField(_('After skin contact'), max_length=150,
                            default='-')
    eye = models.CharField(_('After eye contact'), max_length=150, default='-')
    breathe = models.CharField(_('After breathe in'), max_length=150,
                               default='-')
    swallow = models.CharField(_('After swallow'), max_length=150, default='-')
    disposal = models.TextField(_('Proper disposal'), default='-')
    ext_phone = models.CharField(
        _('External help number'), max_length=20, default='0-112'
    )
    int_phone = models.CharField(
        _('Internal help number'), max_length=20, default='10'
    )
    language = models.CharField(_('Language'), max_length=5, default='de')
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    edited = models.DateTimeField(_('Created'), auto_now=True)
    released = models.DateField(_('Released'), blank=True, editable=False,
                                default=None, null=True)

    def __str__(self):
        deps = [x.name for x in self.work_departments.all()]
        return '{} - {}'.format(self.chemical.name, ', '.join(deps))

    class Meta:
        verbose_name = _('Operating instruction draft')
        verbose_name_plural = _('Operating instruction drafts')
        ordering = ['chemical__name']
        permissions = (
            ('create', _('Can create operating instructions')),
            ('release', _('Can release operating instructions')),
        )
