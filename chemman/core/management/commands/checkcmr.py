# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models.safety import HazardStatement, GHSPictogram


class Command(BaseCommand):
    help = 'Check chemicals for CMR substances'

    def handle(self, *args, **opts):
        self.stdout.write('Checking database for CMR substances')
        for base in settings.CMR_HAZARDS:
            q = HazardStatement.objects.select_related().filter(
                ref__startswith=base)
            for h in q.order_by('sortorder'):
                self.stdout.write(' `+ checking for {}:'.format(h))
                for chem in h.chemicals.all():
                    self.stdout.write('  `- found {}'.format(chem))
                    chem.special_log = True
                    chem.cmr = True
                    chem.save()
        pic = GHSPictogram.objects.get(ref_num=6)
        self.stdout.write('Checking database for acutely toxic substances')
        for c in pic.chemicals.all():
            self.stdout.write('`- found {}'.format(c))
            c.special_log = True
            c.save()
