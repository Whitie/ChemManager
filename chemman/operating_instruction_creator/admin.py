# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import (
    WorkDepartment, ProtectionPictogram, OperatingInstructionDraft
)


admin.site.register(WorkDepartment)
admin.site.register(ProtectionPictogram)
admin.site.register(OperatingInstructionDraft)
