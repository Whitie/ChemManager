# -*- coding: utf-8 -*-

import datetime
import decimal
import json


TYPES = {
    'decimal': decimal.Decimal,
    'date': lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date(),
    'datetime': datetime.datetime.fromtimestamp,
    'time': lambda x: datetime.datetime.strptime(x, '%H:%M:%S').time(),
    'timedelta': lambda x: datetime.timedelta(seconds=x),
}


class JSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return dict(__cmtype__='decimal', value=str(obj))
        elif isinstance(obj, datetime.date):
            return dict(__cmtype__='date', value=obj.isoformat())
        elif isinstance(obj, datetime.datetime):
            return dict(__cmtype__='datetime', value=obj.timestamp())
        elif isinstance(obj, datetime.time):
            return dict(__cmtype__='time', value=obj.strftime('%H:%M:%S'))
        elif isinstance(obj, datetime.timedelta):
            return dict(__cmtype__='timedelta', value=obj.total_seconds())
        return json.JSONEncoder.default(self, obj)


def parse_cm_objects(dct):
    if '__cmtype__' in dct:
        return TYPES[dct['__cmtype__']](dct['value'])
    return dct


def dumps(*args, **kw):
    if 'cls' not in kw:
        kw['cls'] = JSONEncoder
    return json.dumps(*args, **kw)


def loads(*args, **kw):
    if 'object_hook' not in kw:
        kw['object_hook'] = parse_cm_objects
    return json.loads(*args, **kw)
