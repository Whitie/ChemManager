# -*- coding: utf-8 -*-

from collections import namedtuple

from django.contrib.auth import authenticate
from django.http import JsonResponse

from core import json_utils


JSONRequest = namedtuple('JSONRequest', 'id method args kwargs')


class JSONError(Exception):
    messages = {
        -32700: 'Parse error',
        -32600: 'Invalid Request',
        -32601: 'Method not found',
        -32602: 'Invalid params',
        -32603: 'Internal error',
        -32000: 'Server error',
        # Own codes
        -32001: 'Authentication required',
        -32002: 'Invalid credentials',
        -32003: 'User is not active',
        -32004: 'Permission error',
    }

    def __init__(self, code, data=None):
        self.code = code
        self.data = data

    @property
    def message(self):
        return self.messages.get(self.code, 'Server error')

    def __str__(self):
        return 'Error: {} ({})'.format(self.code, self.message)

    def to_json(self, data=None):
        json = dict(code=self.code, message=self.message)
        dt = data or self.data
        if dt is not None:
            json['data'] = dt
        return json


class JSONResponseMixin:

    def _parse(self, obj):
        return JSONRequest(
            obj.get('id', None), obj['method'],
            obj.get('args', []), obj.get('kwargs', {})
        )

    def _parse_request(self, req):
        try:
            self.data = json_utils.loads(req.body.decode('utf-8'))
        except Exception as e:
            print(e)
            raise JSONError(-32700)
        try:
            if isinstance(self.data, list):
                self.json_requests = [self._parse(x) for x in self.data]
            else:
                self.json_requests = [self._parse(self.data)]
        except KeyError:
            raise JSONError(-32600)

    def render_to_json_response(self, context, **response_kwargs):
        data = self._prepare_data(context)
        if isinstance(data, list):
            response_kwargs['safe'] = False
        if 'encoder' not in response_kwargs:
            response_kwargs['encoder'] = json_utils.JSONEncoder
        return JsonResponse(data, **response_kwargs)

    def _prepare_data(self, context):
        if isinstance(context, list) and len(context) == 1:
            context = context[0]
        return context

    def _error(self, error, data=None):
        return self.render_to_json_response(
            dict(error=error.to_json(data=data))
        )

    def post(self, request, *args, **kw):
        try:
            self._parse_request(request)
        except JSONError as err:
            return self._error(err)
        responses = []
        for req in self.json_requests:
            method = self._get_method(req.method)
            if method is None:
                return self._error(JSONError(-32601))
            resp = {}
            try:
                resp['result'] = method(request, *req.args, **req.kwargs)
                if req.id:
                    resp['id'] = req.id
                responses.append(resp)
            except Exception as err:
                responses.append(
                    dict(error=JSONError(-32603).to_json(str(err)))
                )
        return self.render_to_json_response(responses)

    def _get_method(self, name):
        # Don't allow internal methods
        name = name.strip('_')
        return getattr(self, name, None)

    def authenticate(self, req, username, password):
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                req.rpc_user = user
                return user.id
            else:
                raise JSONError(-32003)
        else:
            raise JSONError(-32002)
