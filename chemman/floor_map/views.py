# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from core.json_utils import dumps
from core.models.storage import Building
from core.utils import base_menu, MenuItem, render, render_json
from .forms import ViewFloorForm
from .models import Floor, FloorStorage


floor_item = MenuItem(_('Storage Map'), urlname='fm:index')
base_menu.insert(floor_item, 3)


def _get_json_data():
    buildings = Building.objects.all()
    data = {}
    for building in buildings:
        data[str(building.id)] = list(map(
            str, building.floors.values_list('level', flat=True)
        ))
    return dumps(data)


def _get_json_storages(floor):
    storages = {}
    for s in floor.storages.all():
        storages[str(s.id)] = (
            dict(name=s.storage.name, x=s.x, y=s.y, sid=s.id,
                 url=reverse('core:storage-inventory',
                             kwargs={'storage_id': s.storage.id}))
        )
    return dumps(storages)


def index(req):
    form = ViewFloorForm(req.GET)
    ctx = dict(title=_('Floor Map'), json_data=_get_json_data(), show=False,
               form=form)
    if form.is_valid():
        ctx['show'] = True
        cd = form.cleaned_data
        ctx['building'] = cd['building']
        ctx['floor'] = Floor.objects.get(building=cd['building'],
                                         level=cd['level'])
        ctx['storages'] = _get_json_storages(ctx['floor'])
    return render(req, 'floor_map/index.html', ctx)


@login_required
def edit_map(req, floor_id):
    floor = Floor.objects.select_related().get(pk=int(floor_id))
    ctx = dict(title=_('Edit Map'), floor=floor, building=floor.building,
               storages=_get_json_storages(floor))
    return render(req, 'floor_map/edit_map.html', ctx)


def save_coords(req):
    try:
        fs = FloorStorage.objects.get(pk=int(req.GET['sid']))
        fs.x = int(req.GET['x'])
        fs.y = int(req.GET['y'])
        fs.save()
        return render_json(req, {'message': _('<b>Position saved</b>')})
    except Exception as err:
        error = _('Error: {}').format(err)
        return render_json(req, {'message': error})
