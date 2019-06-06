#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import cherrypy
import django

from argparse import ArgumentParser

from django.conf import settings
from cherrypy.process.plugins import Daemonizer, PIDFile

from chemman.wsgi import application

os.environ['DJANGO_SETTINGS_MODULE'] = 'chemman.settings'

django.setup()

DEFAULT_PIDFILE = os.path.join(settings.BASE_DIR, 'chemman.pid')
FAVICON = os.path.join(
    settings.BASE_DIR, 'core', 'static', 'core', 'img', 'ghs07.ico'
)
DEFAULT_PRESENTATION_PATH = os.path.normpath(
    os.path.join(settings.BASE_DIR, '..', 'presentations')
)
PS_URL = settings.PRESENTATION_URL


class ChemManagerApplication:

    def __init__(self, host='0.0.0.0', port=8800):
        self.host = host
        self.port = port

    def add_favicon(self, path):
        config = {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': path,
        }
        cherrypy.tree.mount(None, '/favicon.ico', {'/': config})

    def mount_static(self, url, root, additional_config=None):
        config = {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': root,
            'tools.expires.on': True,
            'tools.expires.secs': 86400,
        }
        if additional_config is not None:
            config.update(additional_config)
        cherrypy.tree.mount(None, url, {'/': config})

    def run(self, daemon=False, pidfile='', log_screen=False, access_log='',
            error_log=''):
        if os.name != 'nt' and daemon:
            Daemonizer(cherrypy.engine).subscribe()
            if not pidfile:
                pidfile = DEFAULT_PIDFILE
        if pidfile:
            PIDFile(cherrypy.engine, pidfile).subscribe()
        cherrypy.config.update({
            'server.socket_host': self.host,
            'server.socket_port': self.port,
            'server.thread_pool': 30,
            'engine.autoreload.on': False,
            'checker.on': False,
            'tools.log_headers.on': False,
            'log.screen': log_screen,
            'log.access_file': access_log,
            'log.error_file': error_log,
        })
        cherrypy.log('Mounting static dir to %s' % settings.STATIC_URL)
        self.mount_static(settings.STATIC_URL, settings.STATIC_ROOT)
        cherrypy.log('Mounting media dir to %s' % settings.MEDIA_URL)
        self.mount_static(settings.MEDIA_URL, settings.MEDIA_ROOT)
        self.add_favicon(FAVICON)
        cherrypy.log('Loading and serving ChemManager application')
        cherrypy.tree.graft(application, '/')
        if not daemon:
            self._subscribe_handlers()
        cherrypy.engine.start()
        cherrypy.engine.block()

    def _subscribe_handlers(self):
        if hasattr(cherrypy.engine, 'signal_handler'):
            cherrypy.engine.signal_handler.subscribe()
        if hasattr(cherrypy.engine, 'console_control_handler'):
            cherrypy.engine.console_control_handler.subscribe()


def main():
    p = ArgumentParser(description='Start ChemManager.')
    p.add_argument('-H', '--host', default='0.0.0.0', help='IP address or '
                   'name to listen on [%(default)s]')
    p.add_argument('-p', '--port', type=int, default=8800, help='Port '
                   'to use [%(default)s]')
    p.add_argument('-P', '--pidfile', default=DEFAULT_PIDFILE, help='Use '
                   'another PID file [%(default)s]')
    p.add_argument('-n', '--no-pidfile', default=False, action='store_true',
                   help='Do not write a PID file [default is to write one]')
    p.add_argument('-d', '--daemon', default=False, action='store_true',
                   help='Daemonize process (Linux only) [%(default)s]')
    p.add_argument('-l', '--log-screen', action='store_true', default=False,
                   help='Print log messages to STDOUT [%(default)s]')
    p.add_argument('-a', '--access-log', dest='access', default='',
                   help='File for access log [disabled]')
    p.add_argument('-e', '--error-log', dest='error', default='',
                   help='File for error log [disabled]')
    p.add_argument(
        '-s', '--serve-presentations', dest='presentations', default=False,
        action='store_true', help='Serve the presentations for ChemManager '
        'under {url} [%(default)s]'.format(url=PS_URL)
    )
    p.add_argument(
        '-b', '--presentations-base', dest='base',
        default=DEFAULT_PRESENTATION_PATH,
        help='Use another base path for presentations [%(default)s]'
    )
    args = p.parse_args()
    app = ChemManagerApplication(args.host, args.port)
    pidfile = '' if args.no_pidfile else args.pidfile
    access = os.path.abspath(args.access) if args.access else ''
    error = os.path.abspath(args.error) if args.error else ''
    if args.presentations:
        if not os.path.exists(os.path.join(args.base, 'index.html')):
            cherrypy.log('Index file for presentations not found.')
            cherrypy.log('*** Disabling presentations ***')
        else:
            cherrypy.log('Mounting presentations to {url}'.format(url=PS_URL))
            app.mount_static(PS_URL, args.base,
                             {'tools.staticdir.index': 'index.html'})
    app.run(args.daemon, pidfile, args.log_screen, access, error)


if __name__ == '__main__':
    main()
