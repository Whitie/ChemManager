# -*- coding: utf-8 -*-

from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from core.models.chems import Chemical
from core.models.safety import (
    EUHazardStatement, GHSPictogram, HazardStatement, PrecautionaryStatement
)
from core.models.storage import Barcode, Order

from .mixins import JSONResponseMixin, JSONError


@method_decorator(csrf_exempt, name='dispatch')
class ChemicalView(JSONResponseMixin, View):

    def get_chemicals(self, req):
        chems = []
        for c in Chemical.objects.filter(active=True).order_by('name'):
            chems.append(
                dict(name=c.display_name, id=c.id, formula=c.formula,
                     special_log=c.special_log)
            )
        return chems

    def get_chemical(self, req, chem_id):
        chem = Chemical.objects.get(pk=chem_id)
        return dict(cmr=chem.cmr, structure_url=chem.structure.url)

    def get_safety_info(self, req, chem_id):
        pass

    def get_safety(self, req):
        safety = dict(euh=[], h=[], p=[], pics=[])
        for h in HazardStatement.objects.all().order_by('sortorder'):
            safety['h'].append(h.to_dict())
        for euh in EUHazardStatement.objects.all().order_by('sortorder'):
            safety['euh'].append(euh.to_dict())
        for p in PrecautionaryStatement.objects.all().order_by('sortorder'):
            safety['p'].append(p.to_dict())
        for pic in GHSPictogram.objects.all().order_by('ref_num'):
            safety['pics'].append(pic.to_dict())
        return safety


@method_decorator(csrf_exempt, name='dispatch')
class DeliveryView(JSONResponseMixin, View):
    permissions = 'core.can_store'

    def _check_permissions(self, user):
        if not user.has_perm(self.permissions):
            raise JSONError(-32004)

    def get_open_orders(self, req):
        self._check_permissions(req.rpc_user)
        _orders = Order.objects.filter(complete=False).order_by('-sent')
        orders = []
        for order in _orders:
            orders.append(
                dict(id=order.id, barcode=order.barcode.code,
                     count=order.count, user=order.user.username,
                     stored=order.stored, sent=order.sent,
                     delivered_count=order.delivered_count)
            )
        return orders

    def search_barcode(self, req, code):
        self._check_permissions(req.rpc_user)
        try:
            bc = Barcode.objects.get(code=code)
        except Barcode.DoesNotExist:
            return None
        return dict(ident=bc.ident, content=bc.content, unit=bc.unit,
                    chemical=bc.chemical.id,
                    stored_chemical=bc.stored_chemical.id)

    def test(self, req, s):
        return 'Hello {}'.format(s)

    def test_restricted(self, req, s):
        self._check_permissions(req.rpc_user)
        return 'Restricted: Hello {}'.format(s)


@method_decorator(csrf_exempt, name='dispatch')
class LabelPrinterView(JSONResponseMixin, View):
    pass
