# -*- coding: utf-8 -*-

import json
import pprint
import os

from decimal import Decimal
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models.chems import Chemical, StorageClass, Synonym
from core.models.safety import (
    EUHazardStatement, GHSPictogram, HazardStatement, PrecautionaryStatement
)


def D(v):
    if v is not None:
        return Decimal(str(v))


def _add_statements(c, chem):
    for euh_num in c['euh']:
        try:
            euh = EUHazardStatement.objects.get(ref=euh_num)
            chem.eu_hazard_statements.add(euh)
        except:  # NOQA
            pass
    for h_num in c['h']:
        try:
            h = HazardStatement.objects.get(ref=h_num)
            chem.hazard_statements.add(h)
        except:  # NOQA
            pass
    for p_num in c['p']:
        try:
            p = PrecautionaryStatement.objects.get(ref=p_num)
            chem.precautionary_statements.add(p)
        except:  # NOQA
            pass
    for sym_num in c['symbols']:
        try:
            sym = GHSPictogram.objects.get(ref_num=sym_num)
            chem.pictograms.add(sym)
        except:  # NOQA
            pass
    chem.save()
    return chem


def _add_storage_class(ref, chem):
    try:
        scl = StorageClass.objects.get(value=ref)
        chem.storage_class = scl
    except:  # NOQA
        pass


def _add_synonyms(synonyms, chem):
    for syn in synonyms:
        s = Synonym.objects.create(chemical=chem, name=syn)
        s.save()


def _add_val_temp(val, default=20):
    if not val:
        return None, None
    if len(val) > 1 and val[1] is not None:
        return D(val[0]), int(val[1])
    else:
        return D(val[0]), default


def _add_high_low(val):
    if not val:
        return None, None
    if len(val) > 1 and val[1] is not None:
        return D(val[0]), D(val[1])
    else:
        return D(val[0]), None


def import_one(c, structure_dir, sdb_dir):
    chem = Chemical.objects.create(
        name=c['name'], name_en=c['name_en'], slug=slugify(c['name']),
        iupac_name=c['iupac_de'], iupac_name_en=c['iupac_en'] or '',
        formula=c['formula'], molar_mass=D(c['molmass']),
        whc=c['wgk'] or 0,
        mac=D(c['agw']), mac_unit='mg/m3', mabc=D(c['bgw']),
        mabc_unit='mg/L', ioelv=D(c['ioelv']), hin=c['kemler'],
        ext_media=c['ext_agents'], un_ext_media=c['no_ext_agents'],
        fire_advice=c['fire_misc'],
        added_by=User.objects.get(username='admin')
    )
    chem.update_wiki_link()
    chem.save()
    ident = chem.identifiers
    if 'entzündlich' in c['betrsichv'].lower():
        chem.flammable = True
    if c['structure']:
        path = os.path.join(structure_dir, c['structure'])
        with open(path, 'rb') as fp:
            f = File(fp)
            chem.structure.save(c['structure'], f, save=True)
    if c['signal']:
        sig = c['signal'].lower()
        if sig == 'achtung':
            chem.signal_word = 'warning'
        elif sig == 'gefahr':
            chem.signal_word = 'danger'
    chem = _add_statements(c, chem)
    if c['synonyms']:
        _add_synonyms(c['synonyms'], chem)
    _add_storage_class(c['lgk_trgs510'], chem)
    chem.save()
    ident.cas = c['cas']
    ident.einecs = c['eg_num']
    ident.inchi = c['inchi']
    ident.inchi_key = c['inchikey']
    ident.smiles = c['smiles']
    ident.pubchem_id = c['pc_cid']
    ident.un = c['un']
    ident.save()
    if c['source']:
        path = os.path.join(sdb_dir, c['source'])
        with open(path, 'rb') as fp:
            f = File(fp)
            ident.imported_from.save(c['source'], f, save=True)
    phys = chem.physical_data
    phys.color = c['color']
    phys.odor = c['odor']
    phys.save()
    state = c['state'].lower()
    if state == 'fest':
        phys.physical_state = 's'
    elif state == 'flüssig':
        phys.physical_state = 'l'
    elif state == 'gsförmig':
        phys.physical_state = 'g'
    phys.density, phys.density_temp = _add_val_temp(c['density'])
    phys.bulk_density, _ = _add_val_temp(c['bulk_density'])
    phys.melting_point_low, phys.melting_point_high = _add_high_low(
        c['melting']
    )
    phys.boiling_point_low, phys.boiling_point_high = _add_high_low(
        c['boiling']
    )
    phys.save()


class Command(BaseCommand):
    help = 'Import chemicals from SDB parser JSON output'

    def add_arguments(self, parser):
        parser.add_argument('data_dir')

    def handle(self, *args, **opts):
        data_dir = os.path.abspath(opts['data_dir'])
        structure_dir = TemporaryDirectory(prefix='ChemMan-Struc-')
        sdb_dir = TemporaryDirectory(prefix='ChemMan-SDB-')
        self._extract(os.path.join(data_dir, 'structures.zip'),
                      structure_dir.name)
        self._extract(os.path.join(data_dir, 'sdbs.zip'), sdb_dir.name)
        with open(os.path.join(data_dir, 'all_cleaned.json')) as fp:
            data = json.load(fp)
        self._import(data, structure_dir.name, sdb_dir.name)
        structure_dir.cleanup()
        sdb_dir.cleanup()

    def _extract(self, zipfilename, dest_dir):
        self.stdout.write('Extracting {} to {}'.format(
            os.path.basename(zipfilename), dest_dir)
        )
        with ZipFile(zipfilename) as zipfp:
            zipfp.extractall(path=dest_dir)

    def _import(self, data, structure_dir, sdb_dir):
        self.stdout.write('Found {} chemicals in record'.format(len(data)))
        for i, c in enumerate(data, start=1):
            self.stdout.write('{}) Importing {}'.format(i, c['name']))
            try:
                import_one(c, structure_dir, sdb_dir)
                self.stdout.write(self.style.SUCCESS(' -> Successfull'))
            except Exception as err:
                self.stdout.write(self.style.ERROR(' -> Error, skipping...'))
                self.stdout.write(str(err))
                pprint.pprint(c)
