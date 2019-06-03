# -*- coding: utf-8 -*-

import logging

import requests

from django.conf import settings
from django.contrib.auth.models import User

from cryptography.fernet import Fernet


logger = logging.getLogger(__name__)


def _create_user(username, password, data):
    user = User(username=username, email=data['email'],
                last_name=data['last_name'], first_name=data['first_name'])
    user.set_password(password)
    user.save()
    user.employee.ozone_id = data['id']
    user.employee.save()
    return user


class OzoneAuthBackend:

    def authenticate(self, username=None, password=None):
        if username is None or password is None:
            return None
        logger.debug('Trying to authenticate with ozone')
        _token = '{uname}{sep}{passwd}'.format(
            uname=username, sep=settings.OZONE_AUTH_SEPARATOR,
            passwd=password
        )
        _token = _token.encode('utf-8')
        fernet = Fernet(settings.OZONE_AUTH_KEY)
        token = fernet.encrypt(_token)
        r = requests.get(settings.OZONE_AUTH_URL, params={'token': token})
        if r.status_code != 200:
            logger.error('Ozone auth URL request returned a status of '
                         '%d', r.status_code)
            return None
        data = r.json()
        if data['success']:
            try:
                user = User.objects.get(username=username)
                user.set_password(password)
                user.employee.ozone_id = data['id']
                user.employee.save()
                user.save()
                logger.info('Login successfull: %s', username)
            except User.DoesNotExist:
                user = _create_user(username, password, data)
                logger.info('User created: %s', username)
            return user
        else:
            logger.error('Login failed: %s', data['message'])
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
