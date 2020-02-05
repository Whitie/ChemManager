# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import permission_required
from django.utils.translation import ugettext_lazy as _

from core.utils import base_menu, Menu, MenuItem, render
from .forms import OIForm
from .models import OperatingInstructionDraft


oic_item = MenuItem(_('Operating Instructions'), urlname='oic:index')
base_menu.add(oic_item)
oic_menu = Menu(
    _('Op. Inst.'),
    MenuItem(_('New'), urlname='oic:index'),
)


def index(req):
    drafts = OperatingInstructionDraft.objects.select_related().filter(
        released__isnull=True).order_by('-edited')
    released = OperatingInstructionDraft.objects.select_related().filter(
        released__isnull=False).order_by('-edited')
    ctx = dict(drafts=drafts, released=released, menu=oic_menu)
    return render(req, 'oic/index.html', ctx)


@permission_required('operating_instruction_creator.create')
def edit_operating_instruction(req, id):
    oi = OperatingInstructionDraft.objects.select_related().get(pk=id)
    chem = oi.chemical
    form = OIForm()
    ctx = dict(oi=oi, chem=chem, form=form)
    return render(req, 'oic/edit.html', ctx)


@permission_required('operating_instruction_creator.release')
def release(req, id):
    oi = OperatingInstructionDraft.objects.select_related().get(pk=id)
    chem = oi.chemical
