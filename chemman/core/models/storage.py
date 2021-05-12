# -*- coding: utf-8 -*-

import datetime

from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, pgettext_lazy

from .base import Company, Department, Group
from .chems import Chemical
from .. import units


TYPE_CHOICES = (
    ('general', _('General Storage')),
    ('through', _('Through Storage')),
    ('solids', _('Solids Storage')),
    ('solvents', _('Solvent Storage')),
)
UNIT_CHOICES = (
    ('g', _('g')),
    ('µg', _('µg')),
    ('mg', _('mg')),
    ('kg', _('kg')),
    ('mL', _('mL')),
    ('L', _('L')),
)
MASS_CHOICES = (
    ('g', _('g')),
    ('µg', _('µg')),
    ('mg', _('mg')),
    ('kg', _('kg')),
)
VOLUME_CHOICES = (
    ('mL', _('mL')),
    ('L', _('L')),
)
CONTAINER_MATERIAL_CHOICES = (
    ('plastic', _('Plastic')),
    ('glass', _('Glass')),
    ('alu', _('Aluminium')),
    ('carton', _('Carton')),
    ('bag', _('Bag')),
    ('canister', _('Canister')),
    ('hobbock', _('Hobbock')),
    ('barrel', _('Barrel')),
    ('pallet', _('Pallet')),
)
QUALITY_CHOICES = (
    ('selfmade', _('Self made')),
    ('technical', _('technically')),
    ('synthesis', _('for synthesis')),
    ('purest', _('purest')),
    ('pheur', _('Ph. Eur.')),
    ('analysis', _('for analysis')),
    ('special', _('special')),
)
COMPOSITION_CHOICES = (
    ('liquid', _('liquid')),
    ('semi-solid', _('semi-solid')),
    ('micronized', _('micronized')),
    ('powdered', _('powdered')),
    ('crystalline', _('crystalline')),
    ('granules', _('Granules')),
)
LIMIT_CHOICES = (
    ('min', _('Minimum')),
    ('max', _('Maximum')),
)


class Building(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    identifier = models.CharField(_('Identifier'), max_length=10, blank=True)
    street = models.CharField(_('Street'), max_length=100)
    zip_code = models.CharField(_('ZIP Code'), max_length=20)
    city = models.CharField(_('City'), max_length=100)
    country = models.CharField(_('Country'), max_length=100)
    notes = models.TextField(_('Notes'), blank=True)

    def __str__(self):
        return '{} ({})'.format(self.name, self.street)

    class Meta:
        verbose_name = _('Building')
        verbose_name_plural = _('Buildings')
        ordering = ['name']


class Storage(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    building = models.ForeignKey(
        Building, verbose_name=_('Building'), related_name='storages',
        on_delete=models.CASCADE
    )
    department = models.ForeignKey(
        Department, verbose_name=_('Department'), related_name='storages',
        on_delete=models.CASCADE
    )
    type = models.CharField(_('Type'), max_length=10, choices=TYPE_CHOICES)
    consumption = models.BooleanField(_('Consumption'), default=False)
    observe = models.BooleanField(_('Observe'), default=False)
    lockable = models.BooleanField(_('Lockable'), default=False)

    def __str__(self):
        return '{}, {} ({})'.format(self.name, self.department.name,
                                    self.get_type_display())

    @property
    def responsible_employee(self):
        return [x.user for x in self.department.employee.all()]

    class Meta:
        verbose_name = _('Storage')
        verbose_name_plural = _('Storages')
        ordering = ['department__name', 'name']
        permissions = (
            ('can_store', _('Can store chemicals')),
            ('can_consume', _('Can consume chemicals')),
            ('can_transfer', _('Can transfer chemicals')),
            ('can_dispose', _('Can dispose chemicals')),
            ('set_limits', _('Can set stocklimits')),
            ('manage_storage', _('Can manage chemicals, limits...')),
            ('inventory', _('Can make inventory')),
        )


class Room(models.Model):
    name = models.CharField(_('Name'), max_length=100, blank=True)
    number = models.CharField(_('Number'), max_length=15, blank=True)
    building = models.ForeignKey(
        Building, verbose_name=_('Building'), related_name='rooms',
        on_delete=models.CASCADE
    )
    storage = models.ForeignKey(
        Storage, verbose_name=_('Storage'), related_name='rooms',
        on_delete=models.CASCADE
    )

    def __str__(self):
        tmp = [self.name or '-', self.number or '-', self.building.name,
               self.storage.name]
        return ', '.join(tmp)

    @property
    def display(self):
        tmp = []
        if self.name:
            tmp.append(self.name)
        if self.number:
            if tmp:
                tmp.append('({})'.format(self.number))
            else:
                tmp.append(self.number)
        if not tmp:
            return _('Unnamed Room')
        return ' '.join(tmp)

    class Meta:
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')
        ordering = ['building', 'storage', 'name']


class StoragePlace(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    storage = models.ForeignKey(
        Storage, verbose_name=_('Storage'), related_name='places',
        on_delete=models.CASCADE
    )
    room = models.ForeignKey(
        Room, verbose_name=_('Room'), blank=True, null=True,
        related_name='places', on_delete=models.CASCADE
    )
    lockable = models.BooleanField(_('Lockable'), default=False)

    def __str__(self):
        return self.name

    @property
    def for_tox(self):
        return self.lockable or self.storage.lockable

    class Meta:
        verbose_name = _('Storage Place')
        verbose_name_plural = _('Storage Places')
        ordering = ['storage', 'name']


class MaterialSafetyDataSheet(models.Model):
    published = models.DateField(_('Published'))
    document = models.FileField(_('Document'), upload_to='msds/%Y/%m')
    last_updated = models.DateField(_('Last Updated'), auto_now=True)

    def __str__(self):
        return self.document.name

    class Meta:
        verbose_name = _('Material Safety Data Sheet')
        verbose_name_plural = _('Material Safety Data Sheets')
        ordering = ['-published']
        permissions = (
            ('can_review', _('Can review MSDS')),
        )

    @property
    def review_required(self):
        now = datetime.date.today()
        age = now - self.last_updated
        return age > datetime.timedelta(days=settings.MSDS_MAXAGE_DAYS)


class StoredChemical(models.Model):
    chemical = models.ForeignKey(
        Chemical, verbose_name=_('Chemical'), related_name='storage',
        on_delete=models.CASCADE
    )
    company = models.ForeignKey(
        Company, verbose_name=_('Company'), related_name='stored_chemicals',
        blank=True, null=True, on_delete=models.SET_NULL
    )
    name_extra = models.CharField(
        _('Name extra'), max_length=100, blank=True
    )
    quality = models.CharField(
        _('Quality'), max_length=15, blank=True, choices=QUALITY_CHOICES,
        default='', help_text=_('Choose special here if no quality match. '
                                'Give exact quality in the extra field.')
    )
    msds = models.ForeignKey(
        MaterialSafetyDataSheet, verbose_name=_('Material Safety Data Sheet'),
        related_name='stored_chemicals', blank=True, null=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return '{}, {} ({})'.format(
            self.chemical.name, self.get_quality_display(),
            getattr(self.company, 'short_name', _('No company'))
        )

    def get_inventory(self, **package_filter):
        package_filter['empty'] = False
        stocks = []
        for p in self.packages.filter(**package_filter):
            stocks.append(p.get_inventory())
        if not stocks:
            return units.Mass(0, 'g')
        start = stocks[0]
        for s in stocks[1:]:
            start += s
        return start

    def get_inventory_for_storage(self, storage):
        return self.get_inventory(place__storage=storage)

    class Meta:
        verbose_name = _('Stored Chemical')
        verbose_name_plural = _('Stored Chemicals')
        ordering = ['chemical']
        unique_together = ('chemical', 'company', 'quality', 'name_extra')


class Barcode(models.Model):
    chemical = models.ForeignKey(
        Chemical, verbose_name=_('Chemical'),
        related_name='barcodes', on_delete=models.CASCADE
    )
    stored_chemical = models.ForeignKey(
        StoredChemical, models.SET_NULL, verbose_name=_('Stored Chemical'),
        related_name='barcodes', blank=True, null=True
    )
    code = models.CharField(_('Code'), max_length=100, unique=True)
    ident = models.CharField(_('Supplier Ident. No.'), max_length=20,
                             blank=True)
    content = models.DecimalField(
        _('Content'), max_digits=9, decimal_places=4, blank=True, null=True
    )
    unit = models.CharField(_('Unit'), max_length=2, choices=UNIT_CHOICES,
                            blank=True)

    def __str__(self):
        if self.stored_chemical:
            return '{} -> {}'.format(self.code, self.stored_chemical)
        return self.code

    @property
    def name(self):
        if self.stored_chemical:
            return str(self.stored_chemical)
        return str(self.chemical)

    class Meta:
        verbose_name = _('Barcode')
        verbose_name_plural = _('Barcodes')
        ordering = ['chemical']


class StoredPackage(models.Model):
    stored_chemical = models.ForeignKey(
        StoredChemical, verbose_name=_('Stored Chemical'),
        related_name='packages', on_delete=models.CASCADE
    )
    place = models.ForeignKey(
        StoragePlace, on_delete=models.CASCADE,
        verbose_name=_('Storage Place'), related_name='packages'
    )
    content = models.DecimalField(_('Content'), max_digits=9,
                                  decimal_places=4)
    unit = models.CharField(_('Unit'), max_length=2, choices=UNIT_CHOICES)
    composition = models.CharField(
        _('Composition'), max_length=15, blank=True, default='',
        choices=COMPOSITION_CHOICES
    )
    container_material = models.CharField(
        _('Container Material'), max_length=10, default='plastic',
        choices=CONTAINER_MATERIAL_CHOICES
    )
    # The following field holds the value of content in one of the default
    # units (settings.DEFAULT_MASS_UNIT or settings.DEFAULT_VOLUME_UNIT)
    content_default = models.DecimalField(max_digits=15, decimal_places=5,
                                          editable=False)
    supplier_ident = models.CharField(_('Supplier Ident. No.'), max_length=20,
                                      blank=True)
    supplier_code = models.CharField(_('Supplier Barcode'), max_length=100,
                                     blank=True)
    supplier_batch = models.CharField(_('Supplier Batch No.'), max_length=30,
                                      blank=True)
    best_before = models.DateField(_('Best before'), blank=True, null=True)
    brutto_mass = models.DecimalField(
        _('Brutto Mass'), max_digits=9, decimal_places=4, blank=True,
        null=True, help_text=_('Mass of the unopened package.')
    )
    brutto_mass_unit = models.CharField(_('Brutto Mass Unit'), max_length=2,
                                        choices=MASS_CHOICES, default='g')
    stored_by = models.ForeignKey(
        User, verbose_name=_('Stored by'), editable=False, blank=True,
        null=True, related_name='stored_packages', on_delete=models.SET_NULL
    )
    stored = models.DateTimeField(_('Stored'), auto_now_add=True)
    # This field is only for caching. No database lookups should be
    # necessary to get the package_id.
    chemical_id = models.PositiveIntegerField(editable=False)
    empty = models.BooleanField(_('Empty'), default=False)
    consume_archived = models.BooleanField(editable=False, default=False)
    disposed_by = models.ForeignKey(
        User, verbose_name=_('Stored by'), editable=False, blank=True,
        null=True, on_delete=models.SET_NULL
    )
    dispose_reason = models.CharField(_('Dispose Reason'), max_length=100,
                                      blank=True, default='')

    def __str__(self):
        return '{} {:.2f} {}, {}'.format(
            self.stored_chemical.chemical.name, self.content, self.unit,
            self.package_id
        )

    @property
    def last_usage(self):
        last = self.usage.all().order_by('usage_date').last()
        if last is not None:
            return last.usage_date
        return self.stored

    @property
    def chemical(self):
        return Chemical.objects.get(pk=self.chemical_id)

    @property
    def qrcode_data(self):
        return self.package_id

    @property
    def package_id(self):
        return '#{:%y%m%d}-{}-{}'.format(self.stored, self.chemical_id,
                                         self.id)

    @property
    def content_obj(self):
        if units.is_mass(self.unit):
            return units.Mass(self.content, self.unit)
        else:
            return units.Volume(self.content, self.unit)

    @property
    def blank_obj(self):
        if units.is_mass(self.unit):
            return units.Mass(Decimal(), self.unit)
        else:
            return units.Volume(Decimal(), self.unit)

    @property
    def brutto(self):
        return units.Mass(self.brutto_mass, self.brutto_mass_unit)

    @property
    def current_brutto(self):
        last = self.usage.all().order_by('usage_date').last()
        if last is not None:
            return last.brutto
        return self.brutto

    def get_inventory(self, to_mass=False):
        if units.is_mass(self.unit):
            if self.empty:
                return units.Mass(0, 'g')
            tmp = units.Mass(self.content, self.unit)
        else:
            if self.empty:
                return units.Volume(0, 'L')
            chem = self.stored_chemical.chemical
            tmp = units.Mass(
                units.volume_to_mass(self.content, self.unit, chem), 'g'
            )
        for u in self.usage.all():
            tmp = tmp - u.removed_mass
        if units.is_mass(self.unit):
            return tmp.convert(self.unit)
        elif to_mass:
            return tmp.convert(settings.DEFAULT_MASS_UNIT)
        else:
            vol = units.mass_to_volume(tmp.value, tmp.unit, chem)
            volume = units.Volume(vol, 'mL')
            return volume.convert(self.unit)

    def get_mass(self, unit=None):
        if unit is None:
            unit = settings.DEFAULT_MASS_UNIT
        if units.is_mass(self.unit):
            return units.convert(self.content, self.unit, unit)
        else:
            chem = self.stored_chemical.chemical
            mass = units.volume_to_mass(self.content, self.unit, chem)
            return units.convert(mass, 'g', unit)

    def get_mass_obj(self, unit=None):
        return units.Mass(self.get_mass(unit), unit)

    def save(self, *args, **kw):
        self.content_default = units.convert(self.content, self.unit)
        self.chemical_id = self.stored_chemical.chemical.id
        if not self.brutto_mass:
            if units.is_mass(self.unit):
                content = self.get_mass_obj(self.unit)
            else:
                content = self.get_mass_obj('g')
            brutto = content + units.Mass(50, 'g')
            self.brutto_mass = brutto.value
            self.brutto_mass_unit = brutto.unit
        return super(StoredPackage, self).save(*args, **kw)

    class Meta:
        verbose_name = _('Stored Package')
        verbose_name_plural = _('Stored Packages')
        ordering = ['place', 'stored_chemical']


class PackageUsage(models.Model):
    package = models.ForeignKey(
        StoredPackage, verbose_name=_('Package'), related_name='usage',
        on_delete=models.CASCADE
    )
    mass_after = models.DecimalField(
        _('Mass after usage'), max_digits=9, decimal_places=4, blank=True,
        null=True
    )
    mass_after_unit = models.CharField(_('Mass after Unit'), max_length=2,
                                       choices=MASS_CHOICES, default='g')
    removed_quantity = models.DecimalField(
        _('Removed Quantity'), max_digits=9, decimal_places=4, blank=True,
        null=True
    )
    removed_quantity_unit = models.CharField(
        _('Removed Quantity Unit'), max_length=2, choices=UNIT_CHOICES,
        default='g'
    )
    usage_date = models.DateTimeField(_('Usage Date/Time'), auto_now_add=True)
    # This field stores the user on special chemicals as given by
    # the web form.
    used_by = models.ForeignKey(User, blank=True, null=True, editable=False,
                                default=None, on_delete=models.SET_NULL)
    user = models.ForeignKey(
        User, verbose_name=_('User'), related_name='package_usages',
        blank=True, null=True, on_delete=models.SET_NULL
    )
    group = models.ForeignKey(
        Group, verbose_name=_('Group'), blank=True,
        related_name='used_packages', null=True, on_delete=models.SET_NULL
    )
    task = models.TextField(_('Task'), blank=True)
    is_inventory = models.BooleanField(_('Is Inventory'), default=False)

    def __str__(self):
        removed = Decimal(-1) * self.removed_quantity
        return '{}, {:+f} {}'.format(self.package, removed,
                                     self.get_removed_quantity_unit_display())

    @property
    def removed_mass(self):
        if units.is_mass(self.removed_quantity_unit):
            return units.Mass(self.removed_quantity,
                              self.removed_quantity_unit)
        else:
            return units.Mass(
                units.volume_to_mass(
                    self.removed_quantity, self.removed_quantity_unit,
                    self.package.stored_chemical.chemical
                ),
                'g'
            )

    @property
    def brutto(self):
        return units.Mass(self.mass_after, self.mass_after_unit)

    @property
    def removed(self):
        if units.is_mass(self.removed_quantity_unit):
            return units.Mass(self.removed_quantity,
                              self.removed_quantity_unit)
        else:
            return units.Volume(self.removed_quantity,
                                self.removed_quantity_unit)

    def remove(self, obj):
        self.removed_quantity = obj.value
        self.removed_quantity_unit = obj.unit

    def save(self, *args, **kw):
        _last = PackageUsage.objects.filter(
            package=self.package).order_by('usage_date').last()
        if _last is None:
            last_mass = units.Mass(self.package.brutto_mass,
                                   self.package.brutto_mass_unit)
        else:
            last_mass = _last.brutto
        if self.mass_after:
            mass_after = self.brutto
            removed_quantity = last_mass - mass_after
            self.removed_quantity = removed_quantity.value
            self.removed_quantity_unit = removed_quantity.unit
        else:
            if units.is_mass(self.removed_quantity_unit):
                removed = self.removed
            else:
                removed = units.Mass(
                    units.volume_to_mass(
                        self.removed_quantity, self.removed_quantity_unit,
                        self.package.stored_chemical.chemical
                    ),
                    'g'
                )
            mass_after = last_mass - removed
            self.mass_after = mass_after.value
            self.mass_after_unit = mass_after.unit
        return super(PackageUsage, self).save(*args, **kw)

    class Meta:
        verbose_name = _('Package Usage')
        verbose_name_plural = _('Package Usages')
        ordering = ['package', '-usage_date']


class StockLimit(models.Model):
    chemical = models.ForeignKey(
        Chemical, verbose_name=_('Chemical'),
        related_name='stock_limits', on_delete=models.CASCADE
    )
    storage = models.ForeignKey(
        Storage, verbose_name=_('Storage'), related_name='stock_limits',
        on_delete=models.CASCADE
    )
    type = models.CharField(
        _('Type'), max_length=3, choices=LIMIT_CHOICES
    )
    stock = models.DecimalField(_('Limit'), max_digits=5,
                                decimal_places=1)
    unit = models.CharField(
        _('Unit'), max_length=2, choices=UNIT_CHOICES,
        default='g'
    )

    def __str__(self):
        return '{stock:.1f} {unit}'.format(
            stock=self.stock, unit=self.get_unit_display()
        )

    @property
    def obj(self):
        if units.is_mass(self.unit):
            return units.Mass(self.stock, self.unit)
        else:
            return units.Volume(self.stock, self.unit)

    def get_order_choices(self):
        q = StoredPackage.objects.filter(
            stored_chemical__chemical=self.chemical,
            place__storage=self.storage
        )
        return q.order_by('stored_chemical__chemical__name')

    def reached(self):
        if units.is_mass(self.unit):
            stock = units.Mass(Decimal(), self.unit)
        else:
            stock = units.Volume(Decimal(), self.unit)
        q = dict(stored_chemical__chemical=self.chemical,
                 place__storage=self.storage)
        for package in StoredPackage.objects.select_related().filter(**q):
            stock = stock + package.get_inventory()
        if self.type == 'min':
            return stock < self.obj
        else:
            return stock > self.obj

    class Meta:
        verbose_name = _('Stock Limit')
        verbose_name_plural = _('Stock Limits')
        unique_together = ('chemical', 'storage', 'type')
        ordering = ['storage']


class LegalLimit(models.Model):
    ident = models.CharField(_('Ident'), max_length=5)
    text = models.CharField(_('Name'), max_length=150, blank=True)
    reference = models.CharField(_('Reference'), max_length=150, blank=True)
    buildings = models.ManyToManyField(
        Building, verbose_name=_('Buildings'), related_name='limits'
    )
    chemicals = models.ManyToManyField(
        Chemical, verbose_name=_('Chemicals'), related_name='limits'
    )
    type = models.CharField(
        _('Type'), max_length=3, choices=LIMIT_CHOICES
    )
    threshold = models.DecimalField(_('Threshold'), max_digits=7,
                                    decimal_places=1)
    percent_of_threshold = models.DecimalField(
        _('Percent of Threshold'), max_digits=4, decimal_places=1,
        default=Decimal(2), validators=[MinValueValidator(Decimal(0)),
                                        MaxValueValidator(Decimal(100))]
    )
    stock = models.DecimalField(
        _('Limit'), max_digits=7, decimal_places=1, editable=False
    )
    unit = models.CharField(
        _('Unit'), max_length=2, choices=UNIT_CHOICES,
        default='kg'
    )

    def __str__(self):
        return '{stock:.1f} {unit}'.format(
            stock=self.stock, unit=self.get_unit_display()
        )

    def save(self, *args, **kw):
        self.stock = (
            (self.threshold / Decimal(100)) * self.percent_of_threshold
        )
        return super(LegalLimit, self).save(*args, **kw)

    @property
    def obj(self):
        if units.is_mass(self.unit):
            return units.Mass(self.stock, self.unit)
        else:
            return units.Volume(self.stock, self.unit)

    def threshold_reached(self):
        if units.is_mass(self.unit):
            stock = units.Mass(Decimal(), self.unit)
        else:
            stock = units.Volume(Decimal(), self.unit)
        for b in self.buildings.all():
            for s in b.storages.all():
                q = dict(stored_chemical__chemical__in=self.chemicals.all(),
                         place__storage=s)
                for package in StoredPackage.objects.select_related(
                  ).filter(**q):
                    stock = stock + package.get_inventory()
        if self.type == 'min':
            return stock < self.obj
        else:
            return stock > self.obj

    class Meta:
        verbose_name = _('Legal Limit')
        verbose_name_plural = _('Legal Limits')
        ordering = ['ident']


class InventoryDifference(models.Model):
    package = models.ForeignKey(
        StoredPackage, verbose_name=_('Package'), related_name='differences',
        on_delete=models.CASCADE
    )
    value = models.DecimalField(_('Value'), max_digits=9, decimal_places=4)
    unit = models.CharField(_('Unit'), max_length=2, choices=UNIT_CHOICES)
    saved = models.DateTimeField(_('Saved'), auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_('User'), blank=True,
                             null=True, on_delete=models.SET_NULL)
    note = models.TextField(_('Note'), blank=True)

    def __str__(self):
        return '{}, {:%Y-%m-%d}, {} {}'.format(
            self.package.package_id, self.saved, self.value, self.unit
        )

    def get_obj(self):
        if units.is_mass(self.unit):
            return units.Mass(self.value, self.unit)
        return units.Volume(self.value, self.unit)

    @property
    def age(self):
        delta = timezone.now() - self.saved
        return delta.days

    @property
    def to_old(self):
        return self.age > settings.INVENTORY_MAX_AGE

    class Meta:
        verbose_name = _('Inventory Difference')
        verbose_name_plural = _('Inventory Differences')
        ordering = ['package', 'saved']


class Order(models.Model):
    barcode = models.ForeignKey(
        Barcode, on_delete=models.CASCADE, verbose_name=_('Barcode'),
        related_name='orders'
    )
    count = models.PositiveSmallIntegerField(_('Count'), default=1)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, verbose_name=_('User'),
        related_name='orders', blank=True, null=True
    )
    stored = models.DateTimeField(auto_now_add=True)
    sent = models.DateTimeField(editable=False, blank=True, null=True,
                                default=None)
    delivered_count = models.PositiveSmallIntegerField(
        _('Delivered'), default=0
    )
    last_delivery = models.DateTimeField(
        editable=False, blank=True, null=True, default=None
    )
    complete = models.BooleanField(editable=False, default=False)

    def __str__(self):
        return '{}x {}, {}'.format(self.count, self.barcode, self.user)

    def save(self, *args, **kw):
        if self.count == self.delivered_count:
            self.complete = True
        return super(Order, self).save(*args, **kw)

    def deliver(self, count):
        self.delivered_count += count
        self.last_delivery = timezone.now()
        self.save()

    class Meta:
        verbose_name = pgettext_lazy('Order system', 'Order')
        verbose_name_plural = pgettext_lazy('Order system', 'Orders')
        ordering = ['-stored']
        permissions = (
            ('can_order', _('Can order chemicals')),
        )


class Consume(models.Model):
    stored_chemical = models.ForeignKey(
        StoredChemical, on_delete=models.CASCADE,
        verbose_name=_('Stored Chemical'), related_name='consumes'
    )
    quantity = models.DecimalField(_('Quantity'), max_digits=9,
                                   decimal_places=4)
    unit = models.CharField(_('Unit'), max_length=2, choices=UNIT_CHOICES)
    opened = models.DateField(_('Opened'))
    stored = models.DateField(auto_now_add=True)
    department = models.ForeignKey(
        Department, verbose_name=_('Department'), blank=True, null=True,
        default=None, related_name='consumes', on_delete=models.SET_NULL
    )

    def __str__(self):
        return '{}: {} -> {} {}'.format(
            self.stored, self.stored_chemical.chemical.display_name,
            self.quantity, self.get_unit_display()
        )

    @property
    def content_obj(self):
        if units.is_mass(self.unit):
            return units.Mass(self.quantity, self.unit)
        else:
            return units.Volume(self.quantity, self.unit)

    @property
    def usage_period(self):
        dt = self.stored - self.opened
        return dt.days

    class Meta:
        verbose_name = _('Consume')
        verbose_name_plural = _('Consumes')
        ordering = ['-stored']
