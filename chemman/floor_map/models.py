# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from PIL import Image

from core.models.storage import Building, Storage


MAXWIDTH = 960


# Helper functions

def get_floor_image_path(instance, filename):
    return 'floor_maps/{}/{}_{}'.format(instance.building.id, instance.level,
                                        filename)


def check_map_size(image_path):
    img = Image.open(image_path)
    w, h = img.size
    f = img.format
    if w > MAXWIDTH:
        ratio = MAXWIDTH / w
        size = (MAXWIDTH, h * ratio)
        img = img.resize(size)
        img.save(image_path, format=f)
    return img


# Create your models here.

class Floor(models.Model):
    building = models.ForeignKey(
        Building, verbose_name=_('Building'), related_name='floors',
        on_delete=models.CASCADE
    )
    level = models.IntegerField(_('Level'), default=0)
    name = models.CharField(_('Name'), max_length=100, blank=True)
    map = models.ImageField(_('Map'), upload_to=get_floor_image_path)
    map_h = models.PositiveIntegerField(default=0)
    map_w = models.PositiveIntegerField(default=0)

    def __str__(self):
        if self.name:
            return '{} | {} | {}'.format(self.building, self.level, self.name)
        return '{} | {}'.format(self.building, self.level)

    def save(self, *args, **kw):
        super(Floor, self).save(*args, **kw)
        img = check_map_size(self.map.path)
        self.map_w, self.map_h = img.size
        super(Floor, self).save()

    class Meta:
        verbose_name = _('Floor')
        verbose_name_plural = _('Floors')
        ordering = ['building', 'level']
        unique_together = ('building', 'level')


class FloorStorage(models.Model):
    floor = models.ForeignKey(
        Floor, verbose_name=_('Floor'), related_name='storages',
        on_delete=models.CASCADE
    )
    storage = models.OneToOneField(
        Storage, verbose_name=_('Storage'), related_name='floor',
        on_delete=models.CASCADE
    )
    x = models.IntegerField(_('X'), default=0)
    y = models.IntegerField(_('Y'), default=0)

    def __str__(self):
        return '{} ({}, {})'.format(self.storage, self.x, self.y)

    @property
    def xy(self):
        return self.x, self.y

    @property
    def yx(self):
        return self.y, self.x

    class Meta:
        verbose_name = _('Floor Storage')
        verbose_name_plural = _('Floor Storages')
        ordering = ['storage']
