# -*- coding: utf-8 -*-

import json
import os

from django.core.files import File
from django.core.management.base import BaseCommand

from core.models.safety import GHSPictogram


class Command(BaseCommand):
    help = 'Import GHS pictograms from data dir'

    def add_arguments(self, parser):
        parser.add_argument('data_dir')

    def handle(self, *args, **opts):
        data_dir = os.path.abspath(opts['data_dir'])
        with open(os.path.join(data_dir, 'pictograms.json')) as fp:
            data = json.load(fp)
        for imagepath, d in data:
            ghs = GHSPictogram(**d)
            with open(os.path.join(data_dir, *imagepath), 'rb') as fp:
                f = File(fp)
                ghs.image.save(imagepath[-1], f, save=True)
