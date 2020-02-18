# -*- coding: utf-8 -*-

import json
import os

from tempfile import gettempdir, TemporaryDirectory

from django.conf import settings
from background_task import background

from .msds_parser import prepare, sdbparser, uba
from . import utils
from .models import ParsedData, UploadedMSDS


def _save_result(data, upload):
    upload.data = data
    upload.processed = True
    upload.name = (
        data.get('name', '') or data.get('name_en', '')
        or data.get('art_name', 'no name found (please edit)')
    )
    upload.cas = data.get('cas', '')
    upload.save()
    try:
        utils.import_data(upload)
    except Exception as err:
        print(err)
        obj, _ = ParsedData.objects.get_or_create(upload=upload, cmr=False)


@background(queue='msds')
def parse_new_msds(upload_id):
    upload = UploadedMSDS.objects.get(pk=upload_id)
    upload.in_progress = True
    upload.save()
    workdir = getattr(settings, 'MSDS_PARSER_WORKDIR', gettempdir())
    uba_file = os.path.join(workdir, 'uba.json')
    if not os.path.isfile(uba_file):
        uba.main(workdir)
    tmp = TemporaryDirectory(prefix='msds-')
    print(tmp.name)
    json_file = os.path.join(tmp.name, 'all.json')
    result_file = os.path.join(tmp.name, 'single_chem.json')
    with open(os.path.join(tmp.name, '_sdb.pdf'), 'wb') as fp:
        fp.write(upload.document.read())
    sdbparser.batch_call(tmp.name, [tmp.name], True, uba_file)
    if not os.path.isfile(json_file):
        tmp.cleanup()
        return
    with open(json_file, encoding='utf-8') as fp:
        data = json.load(fp)
    try:
        prepare.prepare_data(data[0], tmp.name)
    except Exception as err:
        print(err)
    if os.path.isfile(result_file):
        with open(result_file, encoding='utf-8') as fp:
            result_data = json.load(fp)
        _save_result(result_data, upload)
    tmp.cleanup()
