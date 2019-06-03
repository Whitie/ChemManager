# -*- coding: utf-8 -*-

import json

from django.db.models import TextField

from .json_utils import JSONEncoder, parse_cm_objects


class JSONField(TextField):

    def to_python(self, value):
        if not value.strip():
            return {}
        return json.loads(value, object_hook=parse_cm_objects)

    def from_db_value(self, value, *args, **kw):
        return self.to_python(value)

    def get_prep_value(self, value):
        return json.dumps(value, indent=2, cls=JSONEncoder)
