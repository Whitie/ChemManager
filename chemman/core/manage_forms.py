# -*- coding: utf-8 -*-

from django import forms

from .models.base import Department, Notification
from .models.storage import Building, Room, Storage, StoragePlace


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['name', 'identifier', 'street', 'zip_code', 'city',
                  'country', 'notes']
        localized_fields = '__all__'


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'users']
        localized_fields = '__all__'


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ['type', 'message', 'timeout']
        localized_fields = '__all__'


class StorageForm(forms.ModelForm):
    class Meta:
        model = Storage
        fields = ['name', 'building', 'department', 'type', 'consumption',
                  'observe', 'lockable']
        localized_fields = '__all__'


class StoragePlaceForm(forms.ModelForm):
    class Meta:
        model = StoragePlace
        fields = ['name', 'description', 'storage', 'room', 'lockable']
        localized_fields = '__all__'


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'number', 'building', 'storage']
        localized_fields = '__all__'
