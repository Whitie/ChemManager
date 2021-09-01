# -*- coding: utf-8 -*-

import requests

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from core.models.chems import Chemical


STRUCTURE_URL = 'https://pubchem.ncbi.nlm.nih.gov/image/imagefly.cgi'


def _get_structure(compound_id):
    data = dict(cid=compound_id, width='300', height='300')
    r = requests.get(STRUCTURE_URL, params=data)
    if r.status_code == 200:
        return r.content
    return ''


class Command(BaseCommand):
    help = 'Try to update Wiki links and structure pics for all chemicals.'

    def handle(self, *args, **opts):
        self.stdout.write('Updating all chemicals:')
        for chem in Chemical.objects.select_related().all():
            self.stdout.write(' `+ Processing {}'.format(chem.display_name))
            if not chem.wiki_link or 'Suche' in chem.wiki_link:
                self.stdout.write('  `+ Updating Wiki link')
                chem.update_wiki_link()
                self.stdout.write(f'   - {chem.wiki_link}')
            if chem.identifiers.pubchem_id and not chem.structure:
                self.stdout.write('  `+ Trying to get structure')
                data = _get_structure(chem.identifiers.pubchem_id)
                if data:
                    fp = ContentFile(data)
                    chem.structure.save(f'{chem.id}_structure.png', fp,
                                        save=True)
            chem.save()
