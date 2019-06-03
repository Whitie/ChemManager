# -*- coding: utf-8 -*-

"""This module can be copied to any location. Nothing in it depends on the
django projects. It is provided for the client side of ChemManager, if you
want to make an application using RPC.

You need to install the requests library (pip install requests) to use it.
"""

import datetime
import decimal
import json

import requests


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


class RpcError(Exception):

    def __init__(self, code, message, data=''):
        self.code = code
        self.message = message
        self.data = data

    def __str__(self):
        msg = '{} ({})'.format(self.message, self.code)
        if self.data:
            msg = '{} -> {}'.format(msg, self.data)
        return msg


class CMRpcProxy:
    counter = 0

    def __init__(self, server_url, session=None):
        self.server_url = server_url
        self.session = session or requests.Session()

    @property
    def request_id(self):
        self.counter += 1
        s = '{}-{}'.format(self.__class__.__name__, self.counter)
        return s

    def _prepare_call(self, method, *args, **kw):
        data = dict(id=self.request_id, method=method)
        if args:
            data['args'] = list(args)
        if kw:
            data['kwargs'] = kw
        return data

    def __getattr__(self, attr):
        def make_request(*args, **kw):
            data = self._prepare_call(attr, *args, **kw)
            r = self.session.post(self.server_url, data=dumps(data))
            r.raise_for_status()
            res = loads(r.text)
            if 'error' in res and res['error']:
                raise RpcError(**res['error'])
            return res
        return make_request

    def batch(self, calls):
        batch_calls = []
        for method, args, kwargs in calls:
            data = self._prepare_call(method, *args, **kwargs)
            batch_calls.append(data)
        r = self.session.post(self.server_url, data=dumps(batch_calls))
        r.raise_for_status()
        return loads(r.text)


def test():
    p = CMRpcProxy('http://127.0.0.1:8000/rpc/chemicals/')
    safety = p.get_safety()['result']
    print(list(safety.keys()))
    print(ascii(safety['pics']))


if __name__ == '__main__':
    test()
