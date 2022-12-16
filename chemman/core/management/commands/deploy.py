import getpass
import pathlib
import shutil
import sys

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string


DEPLOY_DIR = settings.BASE_DIR / 'deploy'
DEFAULT_SOCKET = '/run/chemman.sock'
PRESENTATIONS_DIR = settings.BASE_DIR.parent / 'presentations'
INDEX = PRESENTATIONS_DIR / 'index.html'
FAVICON = settings.STATIC_ROOT / 'core' / 'img' / 'ghs07.ico'


class Command(BaseCommand):
    help = (
        'Check if gunicorn is installed and create config files for '
        'Gunicorn, Nginx and Systemd (only Gunicorn and Django-Q). '
        'Systemd service file for Nginx should come from your Distro.'
    )
    chemman_files = [
        'chemman_cluster.service',
        'chemman.service',
        'chemman.socket',
        'cm_daily.service',
        'cm_daily.timer',
        'nginx.conf',
    ]

    def add_arguments(self, parser):
        user = getpass.getuser()
        parser.add_argument(
            '-p', '--port', type=int, default=80,
            help='Port to use for Nginx, default: %(default)s.'
        )
        parser.add_argument(
            '-H', '--host', help='Domain/IP for Nginx '
            'server_name directive. If not given, we use a catch all name. '
            'Use more than once for more server names.',
            action='append'
        )
        parser.add_argument(
            '--hide-presentations', dest='presentations', default=False,
            action='store_true', help='Do not serve the presentations about '
            'ChemManager. Default is to serve them.'
        )
        parser.add_argument(
            '--http-user', default='http', help='Username of the user '
            'running Nginx (usually http or www-data), default: %(default)s.'
        )
        parser.add_argument(
            '--http-group', default='http', help='Groupname of the group '
            'running Nginx (usually http or www-data), default: %(default)s.'
        )
        parser.add_argument(
            '--nginx-only', default=False, action='store_true',
            help='On systems without Systemd generate only Nginx config, '
            'default is to generate all.'
        )
        parser.add_argument(
            '-u', '--user', default=user, help='User to run Gunicorn, '
            'default: %(default)s.'
        )

    def _check_nginx(self):
        if (path := shutil.which('nginx')):
            self.stdout.write(
                self.style.SUCCESS(f'Nginx executable found at {path}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Nginx not found, install with your '
                                   'package manager')
            )
        return path

    def _check_gunicorn(self):
        if (path := shutil.which('gunicorn')):
            self.stdout.write(
                self.style.SUCCESS(f'Gunicorn wrapper found at {path}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Gunicorn not found, install with: '
                    '"poetry install -E deploy" or '
                    '"pip install gunicorn"'
                )
            )
        return path

    def _run_commands(self):
        self.stdout.write('Running migrations...')
        management.call_command('migrate')
        self.stdout.write('Collecting static files...')
        management.call_command('collectstatic', '--no-input')

    def handle(self, *args, **opts):
        DEPLOY_DIR.mkdir(exist_ok=True)
        self._check_nginx()
        gunicorn_path = self._check_gunicorn()
        hint = gunicorn_path is None
        if not gunicorn_path:
            p = pathlib.Path(sys.executable).parent
            gunicorn_path = p / 'gunicorn'
        # self._run_commands()
        ctx = {
            'base_dir': settings.BASE_DIR,
            'manage_py': settings.BASE_DIR / 'manage.py',
            'port': opts['port'],
            'hosts': opts['host'] or ['_'],
            'user': opts['user'],
            'http_user': opts['http_user'],
            'http_group': opts['http_group'],
            'hide_presentations': opts['presentations'],
            'presentations_root': PRESENTATIONS_DIR,
            'presentations_url': settings.PRESENTATION_URL.rstrip('/'),
            'python': sys.executable,
            'gunicorn': gunicorn_path,
            'hint': hint,
            'socket': DEFAULT_SOCKET,
            'static_root': settings.STATIC_ROOT,
            'static_url': settings.STATIC_URL.rstrip('/'),
            'media_root': settings.MEDIA_ROOT,
            'media_url': settings.MEDIA_URL.rstrip('/'),
            'favicon': FAVICON,
        }
        if not INDEX.is_file():
            ctx['hide_presentations'] = True
        for file in self.chemman_files:
            self._process_template(file, ctx)

    def _process_template(self, template_name, context):
        with_path = f'_deploy/{template_name}'
        template = render_to_string(with_path, context)
        with (DEPLOY_DIR / template_name).open('w', encoding='utf-8') as fp:
            fp.write(template)
