# -*- coding: utf-8 -*-

import os
import sys

import django

from argparse import ArgumentParser
from subprocess import Popen, PIPE, STDOUT

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chemman.settings')

django.setup()


LOGFILE = 'install.log'
DATA_DIR = os.path.abspath('data')
DEFAULT_PASSWORD = '123Abc!§'


def check_cwd_venv():
    if 'VIRTUAL_ENV' not in os.environ:
        print('You are not running in a virtualenv. Exiting...')
        sys.exit(1)
    managepy = os.path.join(os.getcwd(), 'manage.py')
    if not os.path.exists(managepy):
        print('It seems, you are not in the right directory.')
        print('No manage.py found. Exiting...')
        sys.exit(1)


class Installer:

    def __init__(self, args, logfile=LOGFILE):
        self.additional = args.add
        self.load_chems = not args.no_chems
        self.password = args.password
        self.logfile = logfile
        self.fp = open(logfile, 'w', encoding='utf-8')

    def run_managepy(self, command, *args):
        py = sys.executable
        cmd = [py, 'manage.py', command]
        cmd.extend(args)
        process = Popen(cmd, stdout=PIPE, stderr=STDOUT,
                        universal_newlines=True)
        self.fp.write('Running command "{}", PID: {}{}'.format(
            ' '.join(cmd), process.pid, os.linesep))
        for line in process.stdout:
            sys.stdout.write(line + os.linesep)
            sys.stdout.flush()
            self.fp.write(line + os.linesep)
        process.wait()
        self.fp.write('Command finished with returncode: {}{}'.format(
            process.returncode, os.linesep))

    def makedirs(self):
        base = os.path.abspath(os.getcwd())
        for name in ('uploads', 'cache', 'cp_static'):
            path = os.path.join(base, name)
            if not os.path.exists(path):
                sys.stdout.write('Creating dir {}'.format(name))
                os.mkdir(path)

    def create_admin_user(self, password):
        from django.contrib.auth.models import User
        try:
            if User.objects.filter(is_superuser=True, is_active=True).count():
                self.fp.write('Admin account already exist.')
                return
        except:
            pass
        self.fp.write('Creating superuser with username "admin" and')
        self.fp.write('password "{}". Be sure to change it!!'.format(password))
        from django.db import DEFAULT_DB_ALIAS
        User._default_manager.db_manager(DEFAULT_DB_ALIAS).create_superuser(
            username='admin', email='admin@example.com', password=password
        )

    def run(self):
        self.run_managepy('migrate')
        self.create_admin_user(self.password)
        self.run_managepy('loaddata', os.path.join(DATA_DIR, 'lgk_dump.json'))
        self.run_managepy('loaddata',
                          os.path.join(DATA_DIR, 'safety_dump.json'))
        self.run_managepy('importghs', DATA_DIR)
        if self.load_chems:
            self.run_managepy('importchems', DATA_DIR)
        self.run_managepy('checkcmr')
        if self.additional:
            self.run_managepy('loaddata',
                              os.path.join(DATA_DIR, 'bbz_testdata.json'))
        self.makedirs()
        self.fp.close()


def main():
    p = ArgumentParser(description='Load initial data and create admin user.')
    p.add_argument('-a', '--load-additional-data', action='store_true',
                   default=False, dest='add', help='Load additional test '
                   'data (buildings, storages, places, departments, ...), '
                   'default: %(default)s')
    p.add_argument('-n', '--no-chems', action='store_true', default=False,
                   help="Don't load chemicals, default: %(default)s")
    p.add_argument('-p', '--password', default=DEFAULT_PASSWORD,
                   help='Password for the new admin user, default: '
                   '%(default)s')
    args = p.parse_args()
    if args.password == DEFAULT_PASSWORD:
        print('No password given, using the default one. ')
        print('Be sure to change it after installation!')
    check_cwd_venv()
    installer = Installer(args)
    installer.run()


if __name__ == '__main__':
    main()
