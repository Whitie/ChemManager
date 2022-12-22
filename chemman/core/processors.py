# -*- coding: utf-8 -*-

from django.conf import settings
from django.db.models.functions import Lower

from .models import Bookmark


def add_bookmarks(req):
    ctx = dict(bookmarks=[])
    if req.user.is_authenticated:
        ctx['bookmarks'] = Bookmark.objects.filter(user=req.user).order_by(
            Lower('text'))
    return ctx


def add_sql_queries(req):
    from django.db import connection
    return dict(con=connection)


def add_misc_info(req):
    # Query Bookmark as dummy to get used DB
    q = Bookmark.objects.all()
    driver = q.db
    name = settings.DATABASES[driver]['NAME']
    name = name.rsplit('.', 1)[0]
    return dict(
        mirror_db=name.endswith('_test'),
        api_base=req.build_absolute_uri('/api/'),
    )
