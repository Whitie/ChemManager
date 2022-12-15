# -*- coding: utf-8 -*-

import re

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ..fields import JSONField


LGK_RE = re.compile(r'(\d?\.?\d+)\s?([A-Z])?')


class CommonSafety(models.Model):
    ref = models.CharField(_('Reference'), max_length=25)
    text = models.TextField(_('Text'))
    sortorder = models.PositiveIntegerField(_('Sortorder'), editable=False)
    combined = models.BooleanField(_('Combined'), default=False)

    def __str__(self):
        return '{fullref} {text}'.format(fullref=self.fullref, text=self.text)

    @property
    def fullref(self):
        return '{id}{ref}'.format(id=self.identifier, ref=self.ref)

    def to_dict(self):
        return dict(ref=self.ref, text=self.text, sortorder=self.sortorder,
                    combined=self.combined, identifier=self.identifier)

    def save(self, *args, **kw):
        if '+' in self.ref:
            part = self.ref.split('+')[0]
            self.sortorder = int(part.strip()[:3])
            self.combined = True
        else:
            self.sortorder = int(self.ref.strip()[:3])
        return super(CommonSafety, self).save(*args, **kw)

    class Meta:
        abstract = True
        ordering = ['sortorder']


class HazardStatement(CommonSafety):
    identifier = 'H'


class EUHazardStatement(CommonSafety):
    identifier = 'EUH'


class PrecautionaryStatement(CommonSafety):
    identifier = 'P'


class GHSPictogram(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    image = models.FileField(_('Image'), upload_to='ghs')
    ref_num = models.PositiveIntegerField(_('Reference Number'), unique=True)

    def __str__(self):
        return '{short} {name}'.format(short=self.short, name=self.name)

    @property
    def short(self):
        return 'GHS{ref:0>2}'.format(ref=self.ref_num)

    def to_dict(self):
        return dict(name=self.name, ref_num=self.ref_num,
                    image_url=self.image.url)


class StorageRestriction(models.Model):
    ref_num = models.PositiveIntegerField(_('Reference Number'))
    text = models.TextField(_('Text'))
    is_html = models.BooleanField(
        _('Is HTML'), default=False,
        help_text=_('Check this if the text is HTML.')
    )

    def __str__(self):
        return str(self.ref_num)

    def get_text(self):
        if self.is_html:
            return mark_safe(self.text)
        return self.text

    class Meta:
        verbose_name = _('Storage Restriction')
        verbose_name_plural = _('Storage Restrictions')
        ordering = ['ref_num']


class StorageClass(models.Model):
    value = models.CharField(_('Value'), max_length=5, unique=True)
    description = models.CharField(_('Description'), max_length=100)
    store_with = JSONField(_('Storage Restrictions'), blank=True)

    def __str__(self):
        return '{}) {}'.format(self.value, self.description)

    def get_store_with_classes(self):
        d = {}
        for class_, restriction in self.store_with.items():
            d[class_] = StorageRestriction.objects.get(ref_num=restriction)
        return d

    def can_store_with(self, class_):
        if isinstance(class_, StorageClass):
            class_ = class_.value
        if class_ in self.store_with:
            return StorageRestriction.objects.get(
                ref_num=self.store_with[class_]
            )
        return False

    class Meta:
        verbose_name = _('Storage Class')
        verbose_name_plural = _('Storage Classes')
        ordering = ['value']
