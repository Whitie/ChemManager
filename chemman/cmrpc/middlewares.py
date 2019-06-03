# -*- coding: utf-8 -*-

from datetime import timedelta
from hashlib import sha512
from time import time

from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from .models import RpcSession


COOKIE_NAME = 'cmrpc_token'
MAX_AGE = 24 * 60 * 60


def _get_user(token):
    session = RpcSession.objects.filter(token=token).first()
    if session is None:
        return AnonymousUser()
    elif session.saved + timedelta(seconds=MAX_AGE) < timezone.now():
        return AnonymousUser()
    else:
        return session.user


def _get_new_token(req):
    ip = req.META.get('REMOTE_ADDR', '0.0.0.0')
    host = req.META.get('HTTP_HOST', 'localhost')
    tmp = [
        req.rpc_user.username.encode('utf-8'),
        str(time()).encode('utf-8'),
        ip.encode('utf-8'),
        host.encode('utf-8')
    ]
    new_token = sha512(b'::'.join(tmp)).hexdigest()
    if hasattr(req.rpc_user, 'cmrpc_session'):
        session = req.rpc_user.cmrpc_session
    else:
        session = RpcSession(user=req.rpc_user)
    session.token = new_token
    session.save()
    return new_token


class RpcAuthMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path_info.startswith('/rpc/'):
            response = self.get_response(request)
            return response
        try:
            token = request.get_signed_cookie(COOKIE_NAME, max_age=MAX_AGE)
            request.rpc_user = _get_user(token)
        except:
            request.rpc_user = AnonymousUser()
        response = self.get_response(request)
        if request.rpc_user.is_authenticated:
            response.set_signed_cookie(
                COOKIE_NAME, _get_new_token(request), max_age=MAX_AGE
            )
        else:
            response.delete_cookie(COOKIE_NAME)
        return response
