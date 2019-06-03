# -*- coding: utf-8 -*-
#
# Run tests with:
# $ coverage run --source="." manage.py test -v 2 core

from decimal import Decimal as D
from django.contrib.auth.models import User
from django.test import TestCase

from . import units
from .models import Chemical, PhysicalData

# Create your tests here.


class MassTestCase(TestCase):
    def test_units_1(self):
        mass1 = units.Mass(D(50), 'g')
        mass2 = units.Mass(D('0.05'), 'kg')
        self.assertEqual(mass1, mass2)

    def test_units_2(self):
        mass1 = units.Mass(D(150), 'mg')
        mass2 = units.Mass(D(150000), 'µg')
        self.assertEqual(mass1, mass2)


class VolumeTestCase(TestCase):
    def test_units(self):
        vol1 = units.Volume(D('1.15'), 'L')
        vol2 = units.Volume(D(1150), 'mL')
        self.assertEqual(vol1, vol2)


class DensityTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.user.save()
        self.chemical = Chemical.objects.create(
            name='Ethanol', slug='ethanol', added_by=self.user
        )
        self.chemical.save()
        pd = PhysicalData.objects.create(
            chemical=self.chemical, physical_state='liquid', density=D('0.79')
        )
        pd.save()

    def test_to_mass(self):
        mass1 = units.Mass(D(790), 'g')
        mass2 = units.volume_to_mass(D(1000), 'mL', self.chemical)
        self.assertEqual(mass1, units.Mass(mass2, 'g'))

    def tearDown(self):
        self.chemical.delete()
        self.user.delete()
