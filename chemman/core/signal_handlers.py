# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models.base import Employee
from .models.chems import (
    Chemical, Identifiers, PhysicalData
)
from .models.storage import Barcode, StoredPackage, Consume
from .utils import check_cmr, check_toxic, check_flammable


@receiver(post_save, sender=Chemical)
def create_related_objects_for_chemical(sender, instance, created, **kw):
    if created:
        if not hasattr(instance, 'identifiers'):
            Identifiers.objects.create(chemical=instance)
        if not hasattr(instance, 'physical_data'):
            PhysicalData.objects.create(chemical=instance)


@receiver(pre_save, sender=Chemical)
def check_cmr_toxic(sender, instance, **kw):
    try:
        check_cmr(instance)
    except:
        pass
    try:
        check_toxic(instance)
    except:
        pass
    try:
        check_flammable(instance)
    except:
        pass


@receiver(post_save, sender=User)
def create_employee(sender, instance, created, **kw):
    if created:
        if not hasattr(instance, 'employee'):
            Employee.objects.create(user=instance, settings={})


@receiver(post_save, sender=StoredPackage)
def save_barcode(sender, instance, created, **kw):
    if instance.supplier_code:
        bc, bc_created = Barcode.objects.get_or_create(
            chemical=instance.stored_chemical.chemical,
            stored_chemical=instance.stored_chemical,
            code=instance.supplier_code
        )
        if bc_created:
            bc.content = instance.content
            bc.unit = instance.unit
            bc.ident = instance.supplier_ident
            bc.save()


@receiver(post_save, sender=StoredPackage)
def save_consume(sender, instance, using, **kw):
    if instance.empty and not instance.consume_archived:
        c = Consume(
            stored_chemical=instance.stored_chemical,
            quantity=instance.content, unit=instance.unit,
            opened=instance.stored.date()
        )
        if instance.place.storage.department:
            c.department = instance.place.storage.department
        c.save()
        instance.consume_archived = True
        instance.save()
