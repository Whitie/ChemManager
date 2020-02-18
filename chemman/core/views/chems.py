# -*- coding: utf-8 -*-

from collections import OrderedDict

from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext, ugettext_lazy as _
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from .. import utils
from ..filters import list_url
from ..forms import ListGeneratorForm, ProfileForm, SearchPackageForm
from ..models import (
    Bookmark, Chemical, Employee, ListCache, Notification, WHC_CHOICES,
    OperatingInstruction, Department
)
from ..models.handbook import Paragraph
from ..models.safety import (
    HazardStatement, EUHazardStatement, PrecautionaryStatement,
    GHSPictogram
)
from ..utils import make_qrcode, render, render_json
from .helpers import (
    get_packages_for_chemical, search_chemical_by_name, search_package
)


# Create your views here.


def logout_view(req):
    logout(req)
    messages.success(req, _('You are logged out.'))
    return redirect('core:index')


def index(req):
    query = Chemical.objects.all()
    all_count = query.count()
    active_count = query.filter(active=True).count()
    cmr_count = query.filter(cmr=True).count()
    paragraphs = Paragraph.objects.select_related().filter(
        id__in=settings.SHOW_HB_PARAGRAPHS
    )
    chems = query.filter(special_log=True, active=True)
    ctx = dict(title=_('Mainpage'), all_count=all_count, cmr_count=cmr_count,
               active_count=active_count, paragraphs=paragraphs, notes=[],
               chems=chems)
    if req.user.is_authenticated:
        for note in Notification.objects.exclude(seen_by=req.user):
            note.seen_by.add(req.user)
            # note.save()
            ctx['notes'].append(note)
    return render(req, 'core/index.html', ctx)


def search(req, searchstring=None):
    if searchstring is None:
        searchstring = req.POST['search']
    chems = search_chemical_by_name(searchstring)
    title = _('Searchresult for {search}').format(search=searchstring)
    ctx = dict(title=title, searchstring=searchstring, chems=chems)
    return render(req, 'core/searchresult.html', ctx)


def extended_search(req):
    if req.method == 'POST':
        which = req.POST['which']
        if which == 'storage':
            form = SearchPackageForm(req.POST)
            if form.is_valid():
                packages, query = search_package(form.cleaned_data)
                ctx = dict(title=_('Package Search'), packages=packages,
                           query=query, chem=form.cleaned_data['chemical'])
                return render(req, 'core/search/package.html', ctx)
    ctx = dict(title=_('Extended Search'))
    return render(req, 'core/extended_search.html', ctx)


def info(req):
    ctx = dict(title=_('Information'))
    return render(req, 'core/info.html', ctx)


def info_operating_instructions(req):
    deps = Department.objects.all().order_by('name')
    instructions = OrderedDict()
    for dep in deps:
        instructions[dep] = OperatingInstruction.objects.filter(
            department=dep
        ).order_by('chemical__name')
    ctx = dict(title=_('Op. Inst. Info'), instructions=instructions)
    return render(req, 'core/info/operating_instructions.html', ctx)


def info_whc(req):
    info = OrderedDict()
    for num, text in WHC_CHOICES:
        info[text] = {
            'count': Chemical.objects.filter(whc=num).count(),
            'name': _('WHC {num}'.format(num=num)),
            'spec': {'query': {'whc': num}, 'and': [], 'or': []},
        }
    ctx = dict(title=_('WHC Info'), whc=info)
    return render(req, 'core/info/whc.html', ctx)


def info_hp(req):
    hs = OrderedDict()
    euh = OrderedDict()
    ps = OrderedDict()
    for h in HazardStatement.objects.select_related().all():
        hs[h.fullref] = {
            'text': h.text,
            'count': h.chemicals.filter(active=True).count(),
            'spec': {'query': {'hazard_statements__ref': h.ref}, 'and': [],
                     'or': []}
        }
    for h in EUHazardStatement.objects.select_related().all():
        euh[h.fullref] = {
            'text': h.text,
            'count': h.chemicals.filter(active=True).count(),
            'spec': {'query': {'eu_hazard_statements__ref': h.ref}, 'and': [],
                     'or': []}
        }
    for p in PrecautionaryStatement.objects.select_related().all():
        ps[p.fullref] = {
            'text': p.text,
            'count': p.chemicals.filter(active=True).count(),
            'spec': {'query': {'precautionary_statements__ref': p.ref},
                     'and': [], 'or': []}
        }
    ctx = dict(title=_('H + P'), hs=hs, euh=euh, ps=ps)
    return render(req, 'core/info/hp.html', ctx)


def info_ghs(req):
    ghs = OrderedDict()
    for pic in GHSPictogram.objects.all():
        ghs[pic.short] = {
            'obj': pic,
            'count': pic.chemicals.filter(active=True).count(),
            'spec': {'query': {'pictograms__ref_num': pic.ref_num},
                     'and': [], 'or': []}
        }
    ctx = dict(title=_('GHS Pictograms'), ghs=ghs)
    return render(req, 'core/info/ghs.html', ctx)


def detail(req, chem):
    packages = get_packages_for_chemical(chem)
    ctx = dict(title=_('Detail'), chem=chem, packages=packages)
    return render(req, 'core/detail.html', ctx)


def detail_by_id(req, cid):
    chem = Chemical.objects.get(pk=cid)
    return detail(req, chem)


def detail_by_slug(req, slug):
    chem = Chemical.objects.get(slug=slug)
    return detail(req, chem)


def choose_list(req):
    if req.method == 'POST':
        form = ListGeneratorForm(req.POST)
        if form.is_valid():
            s, name = utils.form_to_paramstring(form.cleaned_data)
            return redirect('core:list-chemicals', name=name, param=s)
    else:
        form = ListGeneratorForm()
    q = ListCache.objects.all()
    count = q.count()
    lists = q.order_by('-added')[:10]
    ctx = dict(title=_('Listgenerator'), form=form, lists=lists, count=count)
    return render(req, 'core/choose_list.html', ctx)


def list_chemicals(req, name, param):
    query = utils.paramstring_to_query(param)
    _chems = Chemical.objects.select_related().filter(
        query, active=True).order_by('name')
    chems = []
    for c in _chems:
        if c not in chems:
            chems.append(c)
    ctx = dict(title=_('List'), chems=chems, searchstring='', name=name)
    return render(req, 'core/searchresult.html', ctx)


@login_required
def profile_view(req):
    if not hasattr(req.user, 'employee'):
        emp = Employee.objects.create(user=req.user, settings={})
    else:
        emp = req.user.employee
    if req.method == 'POST':
        form = ProfileForm(req.POST)
        if form.is_valid():
            req.user.first_name = form.cleaned_data['first_name']
            req.user.last_name = form.cleaned_data['last_name']
            req.user.save()
            emp.internal_phone = form.cleaned_data['internal_phone']
            emp.save()
            messages.success(req, _('All data was saved.'))
            return redirect('core:index')
    else:
        initial = dict(
            last_name=req.user.last_name, first_name=req.user.first_name,
            internal_phone=emp.internal_phone
        )
        form = ProfileForm(initial=initial)
    ctx = dict(title=_('Profile'), form=form)
    return render(req, 'core/profile.html', ctx)


# API
@login_required
def api_delete_bookmark(req):
    bookmark_id = int(req.GET['bookmark_id'])
    bookmark = Bookmark.objects.get(pk=bookmark_id)
    bookmark.delete()
    return HttpResponse('success')


@csrf_exempt
def api_login(req):
    if req.method == 'POST':
        username = req.POST.get('username', '').lower()
        passwd = req.POST.get('passwd', '')
        user = authenticate(username=username, password=passwd)
        if user is not None:
            login(req, user)
            return render_json(req, {'success': True})
        else:
            return render_json(req, {'success': False, 'msg': ugettext(
                'Wrong username and/or password.'
            )})
    return render_json(req, {'success': False, 'msg': ugettext(
        'Wrong request method (only POST allowed).'
    )})


@login_required
@csrf_exempt
def add_bookmark(req):
    bm = Bookmark.objects.create(user=req.user, url=req.POST['path'],
                                 text=req.POST['name'])
    bm.save()
    s = '<li><a href="{}">{}</a></li>'.format(bm.url, bm.text)
    return HttpResponse(s)


@csrf_exempt
def api_search(req):
    search = req.POST['search']
    results = []
    chems = search_chemical_by_name(search)
    for chem in chems:
        text = '{}, CAS: {}'.format(chem.formula or '-',
                                    chem.identifiers.cas or '-')
        results.append(
            dict(title=chem.display_name, text=text,
                 url=reverse('core:detail-by-slug',
                             kwargs={'slug': chem.slug}))
        )
    return render_json(req, {'results': results})


@csrf_exempt
def api_autocomplete(req):
    search = req.POST['search']
    results = []
    chems = search_chemical_by_name(search)
    for chem in chems:
        text = '{}, CAS: {}'.format(chem.formula or '-',
                                    chem.identifiers.cas or '-')
        results.append(
            dict(title=chem.display_name, text=text, url='#', id=chem.id)
        )
    return render_json(req, results)


def api_inventory_chemical(req, chem_id):
    chem = Chemical.objects.select_related().get(pk=chem_id)
    packages = get_packages_for_chemical(chem)
    if not packages:
        return render_json(req, {'value': '0.0', 'unit': 'g', 'url': '#'})
    tmp = packages[0].get_inventory()
    for package in packages[1:]:
        tmp = tmp + package.get_inventory()
    result = dict(
        value='{:.2f}'.format(tmp.value), unit=tmp.unit,
        url=reverse('core:chem-inventory', kwargs={'chem_id': chem.id})
    )
    return render_json(req, result)


def api_get_lists(req):
    lists = []
    for l in ListCache.objects.all().order_by('-added')[10:]:
        d = dict(name=l.name, url=list_url(l.json_query, l.name),
                 added=l.added.strftime('%d.%m.%Y %H:%M'))
        lists.append(d)
    return render_json(req, lists)


def api_get_search_form(req):
    which = req.GET.get('which', '')
    if which == 'storage':
        form = SearchPackageForm()
        ctx = dict(form=form, which=which)
        return render(req, 'core/search/package.part.html', ctx)
    return HttpResponse('<strong>Not finished</strong>')


# Images
@cache_page(7 * 24 * 60 * 60)
def chem_qrcode(req, image_format, slug):
    uri = req.build_absolute_uri(
        reverse('core:detail-by-slug', kwargs={'slug': slug})
    )
    img, content_type = make_qrcode(image_format, uri)
    response = HttpResponse(content_type=content_type)
    img.save(response, kind=image_format.upper())
    return response


@cache_page(7 * 24 * 60 * 60)
def package_qrcode(req, image_format, package_id):
    img, content_type = make_qrcode(image_format, package_id.strip())
    response = HttpResponse(content_type=content_type)
    img.save(response, kind=image_format.upper())
    return response
