# -*- coding: utf-8 -*-

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = _('Core')

    def ready(self):
        import core.signal_handlers  # noqa: F401
