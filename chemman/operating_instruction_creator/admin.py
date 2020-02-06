# -*- coding: utf-8 -*-

from django.contrib import admin

from .models import (
    WorkDepartment, ProtectionPictogram, OperatingInstructionDraft,
    FirstAidPictogram
)


admin.site.register(WorkDepartment)
admin.site.register(ProtectionPictogram)
admin.site.register(FirstAidPictogram)
admin.site.register(OperatingInstructionDraft)
