# -*- coding: utf-8 -*-

import logging

import requests

from django.conf import settings
from background_task import background

from .models.base import Employee


logger = logging.getLogger(__name__)


@background(queue='core')
def get_ozone_user_id(cm_user_id):
    employee = Employee.objects.get(user__id=cm_user_id)
    user = employee.user
    if employee.ozone_id:
        logger.debug('Ozone user id for %s: %d', user.username,
                     employee.ozone_id)
        return
    logger.debug('Trying to get Ozone user ID for %s', user.username)
    url = settings.OZONE_UID_URL.format(username=user.username)
    logger.debug('Using URL: %s', url)
    r = requests.get(url)
    if r.status_code != 200:
        logger.error('Ozone returned a status of %d', r.status_code)
        return
    data = r.json()
    if data['uid']:
        employee.ozone_id = data['uid']
        employee.save()
        logger.debug('Ozone user id for %s: %d', user.username,
                     employee.ozone_id)
    else:
        logger.debug('No Ozone user ID found for %s', user.username)
