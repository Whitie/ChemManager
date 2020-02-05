# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext, ugettext_lazy as _
from weasyprint import HTML

from core.models.storage import Storage


@permission_required('core.inventory')
def make_inventory_list(req, storage_id):
    storage = Storage.objects.select_related().get(pk=storage_id)
    places = storage.places.all()
    ctx = dict(storage=storage, places=places, user=req.user,
               now=timezone.now(), root=settings.MEDIA_ROOT.rstrip('/'))
    html_filled = render_to_string('pdf/inventory.html', ctx)
    html = HTML(string=html_filled)
    return HttpResponse(html.write_pdf(), 'application/pdf')
