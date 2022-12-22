# -*- coding: utf-8 -*-

import multiprocessing
import platform
import subprocess
import sys

from pathlib import Path

import core
import django

from django.db import connections
from .models import Chemical


class Hardware:
    byteorder = sys.byteorder
    machine = platform.machine()

    @property
    def processor(self):
        p = platform.processor()
        if p:
            return p
        if (path := Path('/proc/cpuinfo')).is_file():
            with path.open() as fp:
                for line in fp:
                    if line.lower().startswith('model name'):
                        p = line.split(':')[1]
                        return p.strip()
        else:
            try:
                p = subprocess.run(
                    ['wmic', 'cpu', 'get', 'name'], check=True,
                    stdout=subprocess.PIPE
                ).stdout
                return p.strip()
            except subprocess.CalledProcessError:
                pass

    @property
    def cpu_count(self):
        try:
            return multiprocessing.cpu_count() or 1
        except Exception as err:
            print(err)
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
        return platform.platform()

    @property
    def cm_version(self):
        return '{} {}'.format(core.__version__, core.__state__)

    @property
    def database(self):
        db = Chemical._base_manager.db
        wrapper = connections[db]
        version = wrapper.get_database_version()
        name = wrapper.display_name
        return f'{name} {version[0]}.{version[1]}'
