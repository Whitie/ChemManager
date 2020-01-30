# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ..fields import JSONField
from ..json_utils import dumps


NOTIFICATION_TYPE_CHOICES = (
    ('info', _('Information')),
    ('danger', _('Important Information')),
    ('success', _('Message')),
)


class Bookmark(models.Model):
    user = models.ForeignKey(
        User, verbose_name=_('User'), related_name='bookmarks',
        on_delete=models.CASCADE
    )
    url = models.CharField(_('URL'), max_length=100)
    text = models.CharField(_('Text'), max_length=100)

    def __str__(self):
        return '{} ({})'.format(self.url, self.user.username)

    class Meta:
        verbose_name = _('Bookmark')
        verbose_name_plural = _('Bookmarks')
        ordering = ['text']


class Notification(models.Model):
    type = models.CharField(
        _('Type'), max_length=7, choices=NOTIFICATION_TYPE_CHOICES,
        default='warning'
    )
    message = models.TextField(
        _('Message'), help_text=_('You can use HTML in this field.')
    )
    timeout = models.PositiveIntegerField(
        _('Timeout'), default=5,
        help_text=_('After this number of seconds the message will disappear '
                    'from screen. Use 0 to force the user to click it away.')
    )
    seen_by = models.ManyToManyField(
        User, blank=True, verbose_name=_('Seen by'),
        related_name='seen_notifications'
    )
    added_by = models.ForeignKey(
        User, verbose_name=_('Author'), related_name='notifications',
        on_delete=models.CASCADE
    )
    added = models.DateTimeField(_('Added'), auto_now_add=True)

    def __str__(self):
        return '{} - {}'.format(self.get_type_display(),
                                self.added_by.username)

    @property
    def msecs(self):
        return self.timeout * 1000

    @property
    def icon(self):
        if self.type == 'info':
            return 'info-circle'
        elif self.type == 'danger':
            return 'exclamation-circle'
        else:
            return 'coffee'

    @property
    def uikit(self):
        msg = (
            '<i class="uk-icon-{icon}"></i> <p>{message}</p>'
            '{author}, {date:%d.%m.%Y %H:%M}'
        ).format(icon=self.icon, message=self.message, author=self.added_by,
                 date=self.added)
        note = dict(message=msg, status=self.type, timeout=self.msecs,
                    pos='top-right')
        return mark_safe(dumps(note))

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-added']


class ListCache(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    hash = models.CharField(max_length=32, editable=False, unique=True)
    json_query = JSONField(_('JSON Query'))
    added = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('List Cache')
        verbose_name_plural = _('List Caches')
        ordering = ['-added']


class ContactData(models.Model):
    street = models.CharField(_('Street'), max_length=100, blank=True)
    zip_code = models.CharField(_('ZIP Code'), max_length=20, blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)
    country = models.CharField(_('Country'), max_length=100, blank=True)
    phone = models.CharField(_('Phone'), max_length=30, blank=True)
    email = models.EmailField(_('Email'), blank=True)

    class Meta:
        abstract = True


class Company(ContactData):
    name = models.CharField(_('Name'), max_length=100)
    short_name = models.CharField(_('Short Name'), max_length=20, blank=True)
    logo = models.ImageField(_('Logo'), upload_to='logos', blank=True)
    fax = models.CharField(_('Fax Number'), max_length=30, blank=True)
    url = models.URLField(_('Webpage'), blank=True)
    customer_number = models.CharField(_('Customer Number'), max_length=50,
                                       blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')
        ordering = ['name']


class ContactPerson(models.Model):
    company = models.ForeignKey(
        Company, verbose_name=_('Company'), related_name='contact_persons',
        on_delete=models.CASCADE
    )
    last_name = models.CharField(_('Last Name'), max_length=50)
    first_name = models.CharField(_('First Name'), max_length=50, blank=True)
    direct_dialing = models.CharField(_('Direct Dialing'), max_length=30,
                                      blank=True)
    email = models.EmailField(_('Email'), blank=True)
    responsible_for = models.CharField(_('Responsible for'), max_length=50,
                                       blank=True)
    notes = models.TextField(_('Notes'), blank=True)

    def __str__(self):
        return '{}, {} ({})'.format(self.last_name, self.first_name,
                                    self.company.name)

    class Meta:
        verbose_name = _('Contact Person')
        verbose_name_plural = _('Contact Persons')
        ordering = ['company__name', 'last_name']


class Department(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True)
    users = models.ManyToManyField(User, verbose_name=_('Employee'),
                                   related_name='departments', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')
        ordering = ['name']


class Employee(models.Model):
    user = models.OneToOneField(User, verbose_name=_('User'),
                                on_delete=models.CASCADE)
    internal_phone = models.CharField(_('Internal Phone'), max_length=30,
                                      blank=True)
    settings = JSONField(_('Settings'), editable=False)
    ozone_id = models.PositiveIntegerField(editable=False, null=True,
                                           default=None)

    def __str__(self):
        return self.user.username


class Group(models.Model):
    name = models.CharField(_('Name'), max_length=30)
    notes = models.TextField(_('Notes'), blank=True)
    active = models.BooleanField(_('Active'), default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
        ordering = ['name']


class JournalType(models.Model):
    name = models.CharField(_('Name'), max_length=30)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Journal Type')
        verbose_name_plural = _('Journal Types')
        ordering = ['name']


class JournalEntry(models.Model):
    type = models.ForeignKey(
        JournalType, verbose_name=_('Type'), related_name='entries',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User, verbose_name=_('User'), related_name='journal_entries',
        on_delete=models.CASCADE
    )
    message = models.TextField(_('Message'))
    user_message = models.CharField(_('User Message'), max_length=200,
                                    blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    added = models.DateTimeField(_('Added'), auto_now_add=True)

    def __str__(self):
        return self.message

    class Meta:
        verbose_name = _('Journal Entry')
        verbose_name_plural = _('Journal Entries')
        ordering = ['-added']
