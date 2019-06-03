# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import UploadedMSDS, ParsedData

# Register your models here.
admin.site.register(UploadedMSDS)
admin.site.register(ParsedData)
