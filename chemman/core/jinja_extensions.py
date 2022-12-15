# -*- coding: utf-8 -*-

from django.utils.translation import (
    pgettext as django_pgettext,
    npgettext as django_npgettext
)
from jinja2.ext import InternationalizationExtension
from jinja2.utils import markupsafe, pass_context


def collapse_whitespace(message):
    """Collapses consecutive whitespace into a single space"""
    return ' '.join(
        map(lambda s: s.strip(), filter(None, message.strip().splitlines()))
    )


@pass_context
def pgettext(env_context, context, message, **variables):
    rv = django_pgettext(context, message)
    if env_context.eval_ctx.autoescape:
        rv = markupsafe.Markup(rv)
    return rv % variables


@pass_context
def npgettext(env_context, context, singular, plural, number, **variables):
    variables.setdefault('num', number)
    rv = django_npgettext(context, singular, plural, number)
    if env_context.eval_ctx.autoescape:
        rv = markupsafe.Markup(rv)
    return rv % variables


class ChemManagerI18nExtension(InternationalizationExtension):
    def __init__(self, environment):
        super(ChemManagerI18nExtension, self).__init__(environment)
        environment.globals['pgettext'] = pgettext
        environment.globals['npgettext'] = npgettext

    def _parse_block(self, parser, allow_pluralize):
        parse_block = InternationalizationExtension._parse_block
        ref, buffer = parse_block(self, parser, allow_pluralize)
        return ref, collapse_whitespace(buffer)


I18N = ChemManagerI18nExtension
