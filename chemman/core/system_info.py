# -*- coding: utf-8 -*-

import os
import platform
import sys

import core
import django


class Hardware:
    byteorder = sys.byteorder
    machine = platform.machine()
    processor = platform.processor()

    @property
    def cpu_count(self):
        if hasattr(os, 'cpu_count'):
            return os.cpu_count() or 1
        return 1


class Software:
    executable = sys.executable or 'python'
    path = sys.path

    django_version = django.__version__

    @property
    def python(self):
        impl = sys.implementation.name
        version = '.'.join(map(str, sys.version_info[:3]))
        state = sys.version_info[3]
        return 'Python {} {} ({})'.format(version, state, impl)

    @property
    def uname(self):
        return '{0.system} {0.version} on {0.node}'.format(platform.uname())

    @property
    def cm_version(self):
        return '{} {}'.format(core.__version__, core.__state__)
