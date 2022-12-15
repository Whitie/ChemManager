# -*- coding: utf-8 -*-

import time

from hashlib import sha256

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django_q.tasks import async_task

from core.models.chems import Chemical
from core.utils import action_menu, MenuItem, render, render_json
from . import utils
from .forms import ParsedEditForm
from .models import UploadedMSDS, ParsedData
from .tasks import parse_new_msds


msds_item = MenuItem(_('Upload MSDS'), urlname='msds:index')
action_item = MenuItem(_('Add chemical'), urlname='msds:list')
action_menu.add(msds_item)
action_menu.add(action_item)


@login_required
def index(req):
    ctx = dict(title=_('MSDS Upload'))
    return render(req, 'msds/index.html', ctx)


@permission_required('msds_collector.upload')
@csrf_exempt
def upload(req):
    file_hash = sha256(req.FILES['msds_file'].read()).hexdigest()
    try:
        obj = UploadedMSDS.objects.get(hash=file_hash)
        txt = _(
            '<i class="uk-icon-exclamation"></i> '
            '<span style="color:red;">'
            'Object <a href="{}">{}</a> already known'
            '</span>'
        ).format(obj.document.url, obj.name or obj.document.name)
    except UploadedMSDS.DoesNotExist:
        token = sha256(
            file_hash.encode('utf-8') + str(time.time()).encode('utf-8')
        ).hexdigest()
        obj = UploadedMSDS.objects.create(
            hash=file_hash, added_by=req.user, document=req.FILES['msds_file'],
            token=token
        )
        obj.save()
        txt = _(
            '<i class="uk-icon-check"></i> '
            'New object (<a href="{}">{}</a>) saved, processing started...'
        ).format(obj.document.url, obj.document.name)
        async_task(parse_new_msds, obj.id)
    return HttpResponse(txt)


@login_required
def list_uploads(req):
    upload_list = UploadedMSDS.objects.all().order_by('-added')
    paginator = Paginator(upload_list, 25)
    page = req.GET.get('page')
    req.session['new'] = True
    try:
        uploads = paginator.page(page)
    except PageNotAnInteger:
        uploads = paginator.page(1)
    except EmptyPage:
        uploads = paginator.page(paginator.num_pages)
    ctx = dict(title=_('Upload List'), uploads=uploads)
    return render(req, 'msds/list.html', ctx)


@permission_required('msds_collector.upload')
def detail(req, upload_id):
    msds = UploadedMSDS.objects.get(pk=upload_id)
    parsed = ParsedData.objects.get(upload=msds)
    if req.method == 'POST':
        form = ParsedEditForm(req.POST, instance=parsed)
        try:
            form.save()
            messages.success(req, _('Changes saved'))
            return redirect('msds:list')
        except Exception as err:
            messages.error(req, _('Changes not saved: {}').format(str(err)))
    form = ParsedEditForm(instance=parsed)
    ctx = dict(title=_('Edit MSDS'), msds=msds, form=form)
    return render(req, 'msds/detail.html', ctx)


@permission_required('msds_collector.upload')
def save_basics(req):
    try:
        pk = int(req.GET.get('id', 0))
        up = UploadedMSDS.objects.get(pk=pk)
    except Exception as e:
        msg = _('Failed: {}').format(str(e))
        return render_json(req, {'success': False, 'msg': msg})
    up.name = req.GET.get('name', up.name)
    up.cas = req.GET.get('cas', up.cas)
    up.save()
    return render_json(req, {'success': True, 'msg': _('Saved')})


@permission_required('msds_collector.upload')
def delete_upload(req):
    pid = req.GET.get('pid', 0)
    try:
        parsed = ParsedData.objects.get(pk=int(pid))
        utils.cleanup(parsed)
        return render_json(req, {'success': True, 'msg': _('Data deleted')})
    except Exception as e:
        msg = _('Failed: {}').format(str(e))
        return render_json(req, {'success': False, 'msg': msg})


@permission_required('core.manage')
def transfer(req, uid):
    up = UploadedMSDS.objects.select_related().get(pk=uid)
    parsed = up.parsed.first()
    exact, similar = utils.find_similar(parsed)
    ctx = dict(title=_('Transfer to DB'), parsed=parsed, exact=exact,
               similar=similar)
    return render(req, 'msds/transfer/similar.html', ctx)


@permission_required('core.manage')
def add_to_db(req, pid):
    parsed = ParsedData.objects.select_related().get(pk=pid)
    try:
        if req.session.get('new', True):
            chem = utils.add_new(parsed, req.user)
            messages.success(req, _('Chemical added'))
        else:
            chem = utils.merge(parsed, req.session['chem_id'])
            messages.success(req, _('Data merged'))
        # Cleanup uploaded and parsed data on success
        utils.cleanup(parsed)
        messages.info(req, _('Uploaded data was deleted.'))
        return redirect('core:detail-by-id', chem.id)
    except Exception as e:
        raise
        messages.error(req, _('Chemical not added. Error: {}').format(str(e)))
        return redirect('msds:list')


@permission_required('core.manage')
def compare(req, pid, chem_id):
    parsed = ParsedData.objects.select_related().get(pk=pid)
    chem = Chemical.objects.select_related().get(pk=chem_id)
    req.session['new'] = False
    req.session['chem_id'] = chem.id
    data = utils.get_data(chem, parsed)
    ctx = dict(title=_('Comparison'), chem=chem, parsed=parsed, data=data)
    return render(req, 'msds/transfer/compare.html', ctx)
