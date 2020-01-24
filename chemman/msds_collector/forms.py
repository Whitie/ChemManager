# -*- coding: utf-8 -*-

from django.forms import ModelForm

from .models import ParsedData


class ParsedEditForm(ModelForm):
    class Meta:
        model = ParsedData
        exclude = ['structure', 'upload']
        localized_fields = '__all__'
