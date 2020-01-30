# -*- coding: utf-8 -*-

from background_task import background
from .models import UploadedMSDS


@background(queue='msds')
def parse_new_msds(upload_id):
    upload = UploadedMSDS.objects.get(pk=upload_id)
    upload.in_progress = True
    upload.save()
    # Parse MSDS here
