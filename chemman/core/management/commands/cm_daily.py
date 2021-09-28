# -*- coding: utf-8 -*-

import decimal
import re
import requests

import pubchempy as pc

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from core.models.chems import Chemical


STRUCTURE_URL = 'https://pubchem.ncbi.nlm.nih.gov/image/imagefly.cgi'
SEARCH_URL = 'https://www.ncbi.nlm.nih.gov/pccompound'
COMPOUND_re = re.compile(r'.+/compound/(\d+)/?', re.I)
MM_MAX_DIFF = decimal.Decimal('0.1')


def _search_compound_id(cas):
    r = requests.get(SEARCH_URL, params={'term': 'CAS-{cas}'.format(cas=cas)})
    m = COMPOUND_re.search(r.text)
    if m is not None:
        return int(m.group(1))


def _update_chem(cid, chem):
    compound = pc.Compound.from_cid(cid)
    data = compound.to_dict()
    mm_saved = chem.molar_mass or -5
    mm_new = data.get('molecular_weight', 0)
    try:
        if abs(mm_saved - mm_new) > MM_MAX_DIFF:
            chem.identifiers.pubchem_id = None
            return
    except Exception as err:
        print(err)
        return
    if not chem.iupac_name_en:
        chem.iupac_name_en = data.get('iupac_name', '')[:200]
    if not chem.formula:
        chem.formula = data.get('molecular_formula', '')
    if not chem.molar_mass:
        if mm_new:
            chem.molar_mass = decimal.Decimal(mm_new)
    if not chem.identifiers.inchi:
        chem.identifiers.inchi = data.get('inchi', '')
    if not chem.identifiers.inchi_key:
        chem.identifiers.inchi_key = data.get('inchikey', '')
    if not chem.identifiers.smiles:
        chem.identifiers.smiles = data.get('canonical_smiles', '')


def _get_structure(compound_id):
    data = dict(cid=compound_id, width='500', height='500')
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
                self.stdout.write('   - {link}'.format(link=chem.wiki_link))
            if not chem.identifiers.pubchem_id and chem.identifiers.cas:
                self.stdout.write('  `+ Searching Pubchem Compound ID')
                cid = _search_compound_id(chem.identifiers.cas)
                if cid:
                    chem.identifiers.pubchem_id = cid
                    self.stdout.write('   + CID: {cid}'.format(cid=cid))
            if chem.identifiers.pubchem_id:
                self.stdout.write('  `+ Updating from Pubchem')
                try:
                    _update_chem(chem.identifiers.pubchem_id, chem)
                except Exception as error:
                    self.stdout.write(str(error))
            if chem.identifiers.pubchem_id and not chem.structure:
                self.stdout.write('  `+ Trying to get structure')
                data = _get_structure(chem.identifiers.pubchem_id)
                if data:
                    fp = ContentFile(data)
                    self.stdout.write('   - Image downloaded')
                    chem.structure.save(
                        '{id}_structure.png'.format(id=chem.id), fp, save=True
                    )
            chem.identifiers.save()
            chem.save()
