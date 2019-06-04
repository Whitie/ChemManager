# -*- coding: utf-8 -*-

import re

from django.contrib.auth.models import User
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


IMAGE_re = re.compile(r'\[img\s+(?P<img_id>\d+)(\s+)?(?P<width>\d+)?\]',
                      re.IGNORECASE)


def replace_image_bb(text):
    def _get_tag(m):
        img_id = int(m.group('img_id'))
        try:
            img = HandbookImage.objects.get(pk=img_id)
            return img.get_tag(m.group('width'))
        except HandbookImage.DoesNotExist:
            return '[IMAGE (ID: {}) NOT FOUND]'.format(img_id)
    text = IMAGE_re.sub(_get_tag, text)
    return text


# Create your models here.

class Handbook(models.Model):
    title = models.CharField(_('Title'), max_length=100)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Handbook')
        verbose_name_plural = _('Handbooks')
        ordering = ['title']
        permissions = (
            ('can_write_handbook', _('Can write handbook')),
        )


class Chapter(models.Model):
    handbook = models.ForeignKey(
        Handbook, verbose_name=_('Handbook'), related_name='chapters',
        on_delete=models.CASCADE
    )
    title = models.CharField(_('Title'), max_length=100)
    number = models.PositiveIntegerField(_('Number'))
    synopsis = models.TextField(_('Synopsis'), blank=True)

    def __str__(self):
        return '{} - {}'.format(self.number, self.title)

    def safe_synopsis(self):
        return mark_safe(self.synopsis)

    def save(self, *args, **kw):
        self.synopsis = replace_image_bb(self.synopsis)
        super(Chapter, self).save(*args, **kw)

    class Meta:
        verbose_name = _('Chapter')
        verbose_name_plural = _('Chapters')
        ordering = ['number']


class Paragraph(models.Model):
    chapter = models.ForeignKey(
        Chapter, verbose_name=_('Chapter'), related_name='paragraphs',
        on_delete=models.CASCADE
    )
    title = models.CharField(_('Title'), max_length=100)
    number = models.PositiveIntegerField(_('Number'))
    lead = models.TextField(_('Lead'), blank=True)
    text = models.TextField(_('Text'), blank=True)
    author = models.ForeignKey(
        User, verbose_name=_('Author'), editable=False, blank=True, null=True,
        related_name='added_paragraphs', on_delete=models.SET_NULL
    )
    added = models.DateTimeField(_('Added'), auto_now_add=True)
    last_modified = models.DateTimeField(_('Last modified'), auto_now=True)
    last_modified_by = models.ForeignKey(
        User, verbose_name=_('Last modified by'), editable=False, blank=True,
        null=True, related_name='modified_paragraphs', default=None,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return '{}.{} - {}'.format(self.chapter.number, self.number,
                                   self.title)

    def safe_lead(self):
        return mark_safe(self.lead)

    def safe_text(self):
        return mark_safe(self.text)

    def save(self, *args, **kw):
        self.text = replace_image_bb(self.text)
        if self.lead:
            self.lead = replace_image_bb(self.lead)
        super(Paragraph, self).save(*args, **kw)

    class Meta:
        verbose_name = _('Paragraph')
        verbose_name_plural = _('Paragraphs')
        ordering = ['number']


class ChapterComment(models.Model):
    chapter = models.ForeignKey(
        Chapter, verbose_name=_('Chapter'), related_name='comments',
        on_delete=models.CASCADE
    )
    title = models.CharField(_('Title'), max_length=50, blank=True)
    text = models.TextField(_('Text'))
    author = models.ForeignKey(
        User, verbose_name=_('Author'), editable=False, blank=True, null=True,
        related_name='paragraph_comments', on_delete=models.SET_NULL
    )
    added = models.DateTimeField(_('Added'), auto_now_add=True)

    def __str__(self):
        return '{} ({})'.format(self.title or '-', self.author.username)

    class Meta:
        verbose_name = _('Chapter Comment')
        verbose_name_plural = _('Chapter Comments')
        ordering = ['chapter', '-added']
        get_latest_by = 'added'
        permissions = (
            ('can_moderate_comments', _('Can moderate comments')),
        )


class HandbookImage(models.Model):
    image = models.FileField(_('Image'), upload_to='handbook')
    width = models.PositiveIntegerField(
        _('Width'), default=200,
        help_text=_('This width is to show the image inside the text. The '
                    'image tag is generally rendered with a link to the full '
                    'size image.')
    )

    def __str__(self):
        return self.image.name

    def get_tag(self, width=None):
        img_width = width or self.width
        return (
            '<a href="{url}"><img src="{url}" alt="{name}" width="{width}">'
            '</a>'.format(url=self.image.url, name=self.image.name,
                          width=img_width)
        )
