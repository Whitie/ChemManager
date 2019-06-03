# -*- coding: utf-8 -*-

import base64
import os

from datetime import datetime
from decimal import Decimal as D

from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from core.models.chems import Chemical, Identifiers, PhysicalData, Synonym
from core.models.safety import (
    EUHazardStatement, GHSPictogram, HazardStatement, PrecautionaryStatement,
    StorageClass
)
from .models import ParsedData


DATE_FORMATS = ('%Y-%m-%d', '%y-%m-%d', '%d.%m.%Y', '%d.%m.%y')


def _safe(val):
    if val is None:
        return
    elif isinstance(val, int):
        return D(val)
    elif isinstance(val, float):
        return D(str(val))
    elif isinstance(val, D):
        return val


def _list_value(seq, ref=False):
    if len(seq) > 1:
        if ref:
            return _safe(seq[0]), seq[1]
        else:
            return _safe(seq[0]), _safe(seq[1])
    elif len(seq) == 1:
        return _safe(seq[0]), None
    else:
        return None, None


def _parse_date(val):
    for f in DATE_FORMATS:
        try:
            dt = datetime.strptime(val, f)
            return dt.date()
        except:
            pass


def import_data(source):
    pd = ParsedData(upload=source, cmr=False)
    d = source.data
    pd.name_en = d['name_en'][:200]
    pd.producer = d['producer'][:200]
    pd.article_name = d['art_name'][:200]
    pd.article_number = d['art_num'][:64]
    pd.security = d['betrsichv'][:100]
    pd.mac = _safe(d['agw'])
    pd.mabc = _safe(d['bgw'])
    pd.boiling_low, pd.boiling_high = _list_value(d['boiling'])
    pd.bulk_density = _safe(d['bulk_density'])
    pd.cmr = d['cmr']
    pd.color = d['color'][:30]
    pd.density, pd.density_temp = _list_value(d['density'], True)
    pd.einecs = d['eg_num'][:9]
    pd.euh = ', '.join(d['euh'])[:200]
    pd.ext_agents = d['ext_agents']
    pd.no_ext_agents = d['no_ext_agents']
    pd.fire_misc = d['fire_misc']
    pd.formula = d['formula'][:200]
    pd.h = ', '.join(d['h'])[:200]
    pd.inchi = d.get('inchi', '')
    pd.inchi_key = d.get('inchi_key', '')[:30]
    pd.ioelv = _safe(d['ioelv'])
    pd.iupac_name = d['iupac_de'][:200]
    pd.iupac_name_en = d['iupac_en'][:200]
    pd.hin = d['kemler'][:5]
    pd.storage_class = d['lgk_trgs510'][:10]
    pd.melting_low, pd.melting_high = _list_value(d['melting'])
    pd.molar_mass = _safe(d['molmass'])
    pd.odor = d['odor'][:30]
    pd.p = ', '.join(d['p'])[:200]
    pd.pubchem_id = d['pc_cid'] or None
    pd.review_date = _parse_date(d['review_date'])
    if d['signal'] in ('danger', 'warning'):
        pd.signal_word = d['signal']
    else:
        pd.signal_word = ''
    pd.smiles = d.get('smiles', '')
    pd.solubility_h2o, pd.solubility_h2o_temp = _list_value(
        d['solubility_h2o'], True
    )
    pd.physical_state = d['state'][:1]
    pd.structure = d['structure']
    pd.structure_fn = d['structure_fn']
    pd.symbols = ', '.join([str(x) for x in d['symbols']])
    pd.synonyms = '; '.join(d['synonyms'])
    pd.vwvws = d['vwvws']
    pd.whc = d['wgk']
    pd.save()


def find_similar(parsed):
    exact_query = Q(name__iexact=parsed.upload.name)
    if parsed.name_en:
        exact_query |= Q(name_en__iexact=parsed.name_en)
    if parsed.formula:
        exact_query |= Q(formula__iexact=parsed.formula)
    if parsed.upload.cas:
        exact_query |= Q(identifiers__cas__exact=parsed.upload.cas)
    exact = Chemical.objects.select_related(
        ).filter(exact_query).order_by('name')
    similar_query = (
        Q(name__icontains=parsed.upload.name) |
        Q(name_en__icontains=parsed.upload.name)
    )
    if parsed.name_en:
        similar_query |= Q(name_en__icontains=parsed.name_en)
    if parsed.formula:
        similar_query |= Q(formula__icontains=parsed.formula)
    similar = Chemical.objects.select_related(
        ).filter(similar_query).exclude(exact_query).order_by('name')
    return exact, similar


def verbose(instance, name):
    try:
        h = instance._meta.get_field(name).help_text
    except AttributeError:
        h = ''
    try:
        v = instance._meta.get_field(name).verbose_name
    except AttributeError:
        v = _('Synonyms')
    return v, h


def get_data(chem, parsed):
    data = [
        verbose(chem, 'name') + (chem.name, parsed.upload.name),
        verbose(chem, 'name_en') + (chem.name_en, parsed.name_en),
        verbose(chem.identifiers, 'cas') + (chem.identifiers.cas,
            parsed.upload.cas),
        verbose(chem, 'mac') + (chem.mac, parsed.mac),
        verbose(chem, 'mabc') + (chem.mabc, parsed.mabc),
        verbose(chem.physical_data, 'boiling_point_low') + (
            chem.physical_data.boiling_point_low, parsed.boiling_low),
        verbose(chem.physical_data, 'boiling_point_high') + (
            chem.physical_data.boiling_point_high, parsed.boiling_high),
        verbose(chem.physical_data, 'bulk_density') + (
            chem.physical_data.bulk_density, parsed.bulk_density),
        verbose(chem.physical_data, 'color') + (
            chem.physical_data.color, parsed.color),
        verbose(chem.physical_data, 'odor') + (
            chem.physical_data.odor, parsed.odor),
        verbose(chem.physical_data, 'density') + (
            chem.physical_data.density, parsed.density),
        verbose(chem.physical_data, 'density_temp') + (
            chem.physical_data.density_temp, parsed.density_temp),
        verbose(chem.identifiers, 'einecs') + (chem.identifiers.einecs,
            parsed.einecs),
        verbose(chem, 'eu_hazard_statements') + (
            ', '.join([x.ref for x in chem.eu_hazard_statements.all()]),
            parsed.euh),
        verbose(chem, 'hazard_statements') + (
            ', '.join([x.ref for x in chem.hazard_statements.all()]),
            parsed.h),
        verbose(chem, 'precautionary_statements') + (
            ', '.join([x.ref for x in chem.precautionary_statements.all()]),
            parsed.p),
        verbose(chem, 'pictograms') + (
            ', '.join(['{:0>2}'.format(x.ref_num) for x in
                      chem.pictograms.all()]),
            parsed.symbols),
        verbose(chem, 'ext_media') + (chem.ext_media, parsed.ext_agents),
        verbose(chem, 'un_ext_media') + (chem.un_ext_media,
            parsed.no_ext_agents),
        verbose(chem, 'fire_advice') + (chem.fire_advice, parsed.fire_misc),
        verbose(chem, 'formula') + (chem.formula, parsed.formula),
        verbose(chem.identifiers, 'inchi') + (chem.identifiers.inchi,
            parsed.inchi),
        verbose(chem.identifiers, 'inchi_key') + (chem.identifiers.inchi_key,
            parsed.inchi_key),
        verbose(chem, 'ioelv') + (chem.ioelv, parsed.ioelv),
        verbose(chem, 'iupac_name') + (chem.iupac_name, parsed.iupac_name),
        verbose(chem, 'iupac_name_en') + (chem.iupac_name_en,
            parsed.iupac_name_en),
        verbose(chem, 'hin') + (chem.hin, parsed.hin),
        verbose(chem.physical_data, 'melting_point_low') + (
            chem.physical_data.melting_point_low, parsed.melting_low),
        verbose(chem.physical_data, 'melting_point_high') + (
            chem.physical_data.melting_point_high, parsed.melting_high),
        verbose(chem, 'molar_mass') + (chem.molar_mass, parsed.molar_mass),
        verbose(chem.identifiers, 'pubchem_id') + (chem.identifiers.pubchem_id,
            parsed.pubchem_id),
        verbose(chem.identifiers, 'smiles') + (chem.identifiers.smiles,
            parsed.smiles),
        verbose(chem.physical_data, 'solubility_h2o') + (
            chem.physical_data.solubility_h2o, parsed.solubility_h2o),
        verbose(chem.physical_data, 'solubility_h2o_temp') + (
            chem.physical_data.solubility_h2o_temp,
            parsed.solubility_h2o_temp),
        verbose(chem, 'synonyms') + (
            ', '.join([x.name for x in chem.synonyms.all()]),
            parsed.synonyms),
        verbose(chem, 'whc') + (chem.whc, parsed.whc),
    ]
    if chem.storage_class:
        data.append(
            verbose(chem, 'storage_class') + (chem.storage_class.value,
            parsed.storage_class)
        )
    return data


def _add_pictograms(c, syms):
    for sym in syms.split(','):
        if sym.strip():
            try:
                pic = GHSPictogram.objects.get(ref_num=int(sym.strip()))
                c.pictograms.add(pic)
            except GHSPictogram.DoesNotExist:
                pass
    c.save()


def _add_statements(c, m2m, stms, class_):
    for stm in stms.split(','):
        if stm.strip():
            try:
                s = class_.objects.get(ref=stm.strip())
                m2m.add(s)
            except class_.DoesNotExist:
                pass
    c.save()


def _add_storage_class(c, sc):
    try:
        s = StorageClass.objects.get(value=sc.strip())
        c.storage_class = s
        c.save()
    except StorageClass.DoesNotExist:
        pass


def _add_identifiers(c, p):
    ident, _ = Identifiers.objects.get_or_create(chemical=c)
    ident.cas = p.upload.cas
    ident.einecs = p.einecs
    ident.inchi = p.inchi
    ident.inchi_key = p.inchi_key
    ident.smiles = p.smiles
    ident.pubchem_id = p.pubchem_id or None
    ident.save()
    ident.imported_from.save(
        os.path.basename(p.upload.document.name),
        ContentFile(p.upload.document.read())
    )
    ident.save()


def _add_physical_data(c, p):
    phy, _ = PhysicalData.objects.get_or_create(chemical=c)
    phy.physical_state = p.physical_state
    phy.color = p.color
    phy.odor = p.odor
    phy.density = p.density or None
    phy.density_temp = p.density_temp or None
    phy.bulk_density = p.bulk_density or None
    phy.melting_point_low = p.melting_low or None
    phy.melting_point_high = p.melting_high or None
    phy.boiling_point_low = p.boiling_low or None
    phy.boiling_point_high = p.boiling_high or None
    phy.solubility_h2o = p.solubility_h2o or None
    phy.solubility_h2o_temp = p.solubility_h2o_temp or None
    phy.save()


def add_new(parsed, user):
    c = Chemical(name=parsed.upload.name, added_by=user)
    c.name_en = parsed.name_en
    c.slug = slugify(parsed.upload.name)
    c.iupac_name = parsed.iupac_name
    c.iupac_name_en = parsed.iupac_name_en
    c.formula = parsed.formula
    c.molar_mass = parsed.molar_mass
    c.signal_word = parsed.signal_word
    c.save()
    _add_pictograms(c, parsed.symbols)
    _add_statements(c, c.hazard_statements, parsed.h, HazardStatement)
    _add_statements(c, c.eu_hazard_statements, parsed.euh, EUHazardStatement)
    _add_statements(c, c.precautionary_statements, parsed.p,
                    PrecautionaryStatement)
    c.whc = parsed.whc
    c.mac = parsed.mac
    c.mac_unit = 'mg/m3'
    c.mabc = parsed.mabc
    c.mabc_unit = 'mg/L'
    _add_storage_class(c, parsed.storage_class)
    c.ioelv = parsed.ioelv
    c.hin = parsed.hin
    c.ext_media = parsed.ext_agents
    c.un_ext_media = parsed.no_ext_agents
    c.fire_advice = parsed.fire_misc
    if parsed.cmr:
        c.cmr = True
        c.special_log = True
    c.save()
    _add_identifiers(c, parsed)
    _add_physical_data(c, parsed)
    for syn in parsed.synonyms.split(';'):
        if syn.strip():
            s = Synonym.objects.create(chemical=c, name=syn.strip())
    if parsed.structure and parsed.structure_fn:
        c.structure.save(
            parsed.structure_fn,
            ContentFile(base64.b64decode(parsed.structure))
        )
        c.save()
    return c


def merge(parsed, chem_id):
    return Chemical.objects.get(pk=int(chem_id))


def cleanup(parsed):
    upload = parsed.upload
    upload.document.delete(save=False)
    upload.delete()
