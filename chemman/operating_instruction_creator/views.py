# -*- coding: utf-8 -*-

from base64 import b64encode
from io import BytesIO

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageDraw, ImageFont
from weasyprint import HTML

from core.views.helpers import search_chemical_by_name
from core.models.base import Department
from core.models.chems import (
    Chemical, OperatingInstruction
)
from core.utils import base_menu, Menu, MenuItem, render, render_json
from .forms import OIForm, ReleaseForm
from .models import OperatingInstructionDraft, FirstAidPictogram


oic_item = MenuItem(_('Operating Instructions'), urlname='oic:index')
base_menu.add(oic_item)
oic_menu = Menu(
    _('Op. Inst.'),
    MenuItem(_('New'), urlname='oic:index'),
)
SIGNAL_WORDS = {
    'de': {
        'danger': 'Gefahr',
        'warning': 'Achtung',
    },
}


def generate_preview(req, data, chem):
    for block in ('hazards', 'protection', 'conduct', 'first_aid', 'disposal'):
        data[block] = data[block].splitlines()
    fa1 = 'E003' if data['green_cross'] else 'E012'
    data['fa1'] = FirstAidPictogram.objects.get(ident=fa1)
    data['fa2'] = FirstAidPictogram.objects.get(ident='E011')
    data['signal_word'] = SIGNAL_WORDS['de'].get(chem.signal_word, '')
    ctx = dict(user=req.user, font_size=12, chem=chem, now=timezone.now(),
               root=settings.MEDIA_ROOT.rstrip('/'), **data)
    html_filled = render_to_string('oic/pdf/oi-preview.de.html', ctx)
    html = HTML(string=html_filled)
    return html


def generate_released_pdf(user, draft):
    data = {}
    lang = draft.language.lower()
    fa1 = 'E003' if draft.green_cross else 'E012'
    data['fa1'] = FirstAidPictogram.objects.get(ident=fa1)
    data['fa2'] = FirstAidPictogram.objects.get(ident='E011')
    data['pictograms'] = [x for x in draft.chemical.pictograms.all()]
    data['ppics'] = [x for x in draft.protection_pics.all()]
    data['cpics'] = [x for x in draft.conduct_pics.all()]
    data['signal_word'] = SIGNAL_WORDS[lang].get(
        draft.chemical.signal_word, ''
    )
    for num, dep in enumerate(draft.work_departments.all(), start=1):
        data['dep_{}'.format(num)] = dep.name
    ctx = dict(user=user, font_size=12, chem=draft.chemical, draft=draft,
               root=settings.MEDIA_ROOT.rstrip('/'), **data)
    # Todo: Edit template
    tpl = 'oic/pdf/oi.{}.html'.format(lang)
    html_filled = render_to_string(tpl, ctx)
    html = HTML(string=html_filled)
    return html.write_pdf()


def get_error_image():
    text = _('! ERROR !')
    font = ImageFont.load_default()
    img = Image.new('RGB', font.getsize(str(text)), color=(255, 51, 51))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), str(text), fill=(255, 255, 255), font=font,
              align='center')
    img = img.resize((img.width * 8, img.height * 8))
    return img


def _smart_replace(s):
    if not s.strip():
        return '-'
    s = s.replace('\r', '\n')
    s = s.replace('\n\n', '\n')
    return s


def save_draft(draft, data):
    # Todo
    draft.work_departments.set([data['dep_1']])
    if data['dep_2'] and data['dep_2'] != data['dep_1']:
        draft.work_departments.add(data['dep_2'])
    draft.signature = data['signature']
    draft.hazards = _smart_replace(data['hazards'])
    draft.protection = data['protection']
    draft.protection_pics.set(data['protection_pics'])
    draft.eye_protection = data['eye_protection']
    draft.hand_protection = data['hand_protection']
    draft.conduct = data['conduct']
    if data['conduct_pics']:
        draft.conduct_pics.set(data['conduct_pics'])
    draft.green_cross = data['green_cross']
    draft.first_aid = _smart_replace(data['first_aid'])
    draft.skin = data['skin']
    draft.eye = data['eye']
    draft.breathe = data['breathe']
    draft.swallow = data['swallow']
    draft.disposal = _smart_replace(data['disposal'])
    draft.ext_phone = data['ext_phone']
    draft.int_phone = data['int_phone']
    draft.released = None
    draft.msds_date = data['msds_date']
    draft.save()


def save_to_chemical(draft, pdf, data):
    for dep in draft.work_departments.all():
        cm_dep, created = Department.objects.get_or_create(name=dep.name)
        if data['substitutes']:
            oi = data['substitutes']
            data['substitutes'] = None
        else:
            oi = OperatingInstruction.objects.create(
                chemical=draft.chemical, department=cm_dep
            )
        doc = ContentFile(pdf)
        name = '{0}_{1}.pdf'.format(draft.chemical.slug, slugify(dep.name))
        oi.document.save(name, doc, save=False)
        oi.notes = data['note']
        oi.last_updated_by = draft.responsible
        draft.saved_as = oi
        oi.save()
        draft.save()


def index(req):
    drafts = OperatingInstructionDraft.objects.select_related().filter(
        released__isnull=True).order_by('-edited')
    released = OperatingInstructionDraft.objects.select_related().filter(
        released__isnull=False, saved_as__isnull=False).order_by('-edited')
    ctx = dict(drafts=drafts, released=released, menu=oic_menu)
    return render(req, 'oic/index.html', ctx)


@permission_required('operating_instruction_creator.create')
def edit_operating_instruction(req, id):
    oi = OperatingInstructionDraft.objects.select_related().get(pk=id)
    if req.method == 'POST':
        form = OIForm(req.POST)
        if form.is_valid():
            oi.responsible = req.user
            save_draft(oi, form.cleaned_data)
            return redirect('oic:index')
    chem = oi.chemical
    deps = oi.work_departments.all()[:2]
    hpics = [x.id for x in chem.pictograms.all()]
    ppics = [x.id for x in oi.protection_pics.all()]
    cpics = [x.id for x in oi.conduct_pics.all()]
    form = OIForm()
    ctx = dict(oi=oi, chem=chem, form=form, deps=deps, hpics=hpics,
               ppics=ppics, cpics=cpics, menu=oic_menu, edit=True)
    return render(req, 'oic/edit.html', ctx)


@permission_required('operating_instruction_creator.create')
def new_operating_instruction(req, chem_id):
    chem = Chemical.objects.select_related().get(pk=chem_id)
    hpics = [x.id for x in chem.pictograms.all()]
    if req.method == 'POST':
        form = OIForm(req.POST)
        if form.is_valid():
            cd = form.cleaned_data
            oi = OperatingInstructionDraft.objects.create(
                chemical=chem, responsible=req.user, signature=cd['signature']
            )
            save_draft(oi, cd)
            return redirect('oic:index')
    form = OIForm()
    ctx = dict(oi=None, chem=chem, form=form, menu=oic_menu, edit=False,
               hpics=hpics)
    return render(req, 'oic/edit.html', ctx)


@permission_required('operating_instruction_creator.release')
def release(req, id):
    oi = OperatingInstructionDraft.objects.select_related().get(pk=id)
    if req.method == 'POST':
        form = ReleaseForm(req.POST, chem=oi.chemical)
        if form.is_valid():
            try:
                pdf = generate_released_pdf(req.user, oi)
                save_to_chemical(oi, pdf, form.cleaned_data)
                oi.released = timezone.now().date()
                oi.save()
                return redirect('oic:index')
            except Exception as err:
                print(err)
    else:
        form = ReleaseForm(chem=oi.chemical)
    notes = {}
    for o in oi.chemical.operating_instructions.all():
        notes[str(o.id)] = o.notes
    ctx = dict(oi=oi, chem=oi.chemical, form=form, notes=notes)
    return render(req, 'oic/save.html', ctx)


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
        except Exception as err:
            print(err)
    img = get_error_image()
    png = BytesIO()
    img.save(png, format='PNG')
    png.seek(0)
    return HttpResponse(b64encode(png.read()), content_type='image/png')


@csrf_exempt
def select_chemical(req):
    search = req.POST['search']
    results = []
    chems = search_chemical_by_name(search)
    for chem in chems:
        text = '{}, CAS: {}'.format(chem.formula or '-',
                                    chem.identifiers.cas or '-')
        results.append(
            dict(title=chem.display_name, text=text,
                 url=reverse('oic:new',
                             kwargs={'chem_id': chem.id}))
        )
    return render_json(req, {'results': results})


def get_related_text(req, chem_id):
    topic = req.GET.get('topic', '')
    chemical = Chemical.objects.select_related().get(pk=chem_id)
    pic_ids = list(chemical.pictograms.all().values_list('id', flat=True))
    data = dict(same=[], similar=[])
    for entry in OperatingInstructionDraft.objects.filter(
      chemical=chemical).values_list(topic, flat=True):
        if entry.strip(' -') and entry not in data['same']:
            data['same'].append(entry)
    for entry in OperatingInstructionDraft.objects.select_related().filter(
      chemical__pictograms__id__in=pic_ids).exclude(
      chemical=chemical).values_list(topic, flat=True):
        if entry.strip(' -') and entry not in data['similar']:
            data['similar'].append(entry)
    if not data['same']:
        data['same'].append('-')
    if not data['similar']:
        data['similar'].append('-')
    return render_json(req, data)
