# -*- coding: utf-8 -*-

from base64 import b64encode
from io import BytesIO

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from PIL import Image, ImageDraw, ImageFont
from weasyprint import HTML

from core.models.chems import Chemical
from core.utils import base_menu, Menu, MenuItem, render
from .forms import OIForm
from .models import OperatingInstructionDraft, FirstAidPictogram


oic_item = MenuItem(_('Operating Instructions'), urlname='oic:index')
base_menu.add(oic_item)
oic_menu = Menu(
    _('Op. Inst.'),
    MenuItem(_('New'), urlname='oic:index'),
)


def generate_preview(req, data, chem):
    for block in ('hazards', 'protection', 'conduct', 'first_aid', 'disposal'):
        data[block] = data[block].splitlines()
    fa1 = 'E003' if data['green_cross'] else 'E012'
    data['fa1'] = FirstAidPictogram.objects.get(ident=fa1)
    data['fa2'] = FirstAidPictogram.objects.get(ident='E011')
    ctx = dict(user=req.user, font_size=12, chem=chem, now=timezone.now(),
               root=settings.MEDIA_ROOT.rstrip('/'), **data)
    html_filled = render_to_string('oic/pdf/oi-preview.de.html', ctx)
    html = HTML(string=html_filled)
    return html


def get_error_image():
    text = _('! ERROR !')
    font = ImageFont.load_default()
    img = Image.new('RGB', font.getsize(str(text)), color=(255, 51, 51))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), str(text), fill=(255, 255, 255), font=font,
              align='center')
    img = img.resize((img.width * 8, img.height * 8))
    return img


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
    deps = oi.work_departments.all()[:2]
    hpics = [x.id for x in chem.pictograms.all()]
    ppics = [x.id for x in oi.protection_pics.all()]
    form = OIForm()
    ctx = dict(oi=oi, chem=chem, form=form, deps=deps, hpics=hpics,
               ppics=ppics)
    return render(req, 'oic/edit.html', ctx)


@permission_required('operating_instruction_creator.release')
def release(req, id):
    oi = OperatingInstructionDraft.objects.select_related().get(pk=id)
    chem = oi.chemical


def preview(req, chem_id):
    form = OIForm(req.POST)
    if form.is_valid():
        try:
            chem = Chemical.objects.get(pk=chem_id)
            html = generate_preview(req, form.cleaned_data, chem)
            png = BytesIO()
            html.write_png(png)
            png.seek(0)
            return HttpResponse(b64encode(png.read()),
                                content_type='image/png')
        except Exception:
            pass
    img = get_error_image()
    png = BytesIO()
    img.save(png, format='PNG')
    png.seek(0)
    return HttpResponse(b64encode(png.read()), content_type='image/png')
