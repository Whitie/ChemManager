# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from ..forms import HandbookCommentForm, NewChapterForm, NewParagraphForm
from ..models.handbook import (
    Handbook, Chapter, Paragraph, HandbookImage, ChapterComment
)
from ..utils import render


def overview(req):
    handbooks = Handbook.objects.all().order_by('title')
    ctx = dict(title=_('Handbooks'), handbooks=handbooks)
    return render(req, 'core/handbook/overview.html', ctx)


def handbook(req, hb_id):
    handbook = Handbook.objects.select_related().get(pk=int(hb_id))
    ctx = dict(title=handbook.title, handbook=handbook)
    return render(req, 'core/handbook/index.html', ctx)


@permission_required('core.can_write_handbook')
def add_chapter(req, hb_id):
    hb = Handbook.objects.get(pk=int(hb_id))
    if req.method == 'POST':
        form = NewChapterForm(req.POST)
        if form.is_valid():
            Chapter.objects.create(handbook=hb, **form.cleaned_data)
            return redirect('core:hb-handbook', hb_id=hb.id)
    else:
        form = NewChapterForm()
    ctx = dict(title=_('New Chapter'), form=form, hb=hb)
    return render(req, 'core/handbook/add_chapter.html', ctx)


@permission_required('core.can_write_handbook')
def add_paragraph(req, chapter):
    chap = Chapter.objects.select_related().get(pk=int(chapter))
    if req.method == 'POST':
        form = NewParagraphForm(req.POST)
        if form.is_valid():
            p = Paragraph.objects.create(chapter=chap, author=req.user,
                                         **form.cleaned_data)
            return redirect('core:hb-edit-paragraph', paragraph=p.id)
    else:
        form = NewParagraphForm()
    ctx = dict(title=_('New Paragraph'), chap=chap, form=form)
    return render(req, 'core/handbook/add_paragraph.html', ctx)


def chapter(req, hb_id, chapter):
    handbook = Handbook.objects.select_related().get(pk=int(hb_id))
    chapter = Chapter.objects.select_related().get(
        handbook=handbook, number=int(chapter)
    )
    if req.method == 'POST':
        form = HandbookCommentForm(req.POST)
        if form.is_valid() and req.user.is_authenticated():
            cd = form.cleaned_data
            comment = ChapterComment(
                chapter=chapter, title=cd['title'], text=cd['text'],
                author=req.user
            )
            comment.save()
            return redirect('core:hb-chapter', hb_id=handbook.id,
                            chapter=chapter.id)
    else:
        form = HandbookCommentForm()
    title = '{} - {}'.format(handbook.title, chapter.title)
    ctx = dict(title=title, handbook=handbook, chapter=chapter, form=form,
               no_title=_('No title'))
    return render(req, 'core/handbook/chapter.html', ctx)


def edit_paragraph(req, paragraph):
    p = Paragraph.objects.select_related().get(pk=int(paragraph))
    if req.method == 'POST':
        p.text = req.POST['text'].strip()
        lead = req.POST['lead'].strip()
        if lead:
            p.lead = lead
        p.last_modified_by = req.user
        p.save()
        return redirect('core:hb-handbook', hb_id=p.chapter.handbook.id)
    ctx = dict(title=_('Edit Paragraph'), paragraph=p,
               images=HandbookImage.objects.all())
    return render(req, 'core/handbook/edit.html', ctx)


# API

@permission_required('core.add_handbook')
def add_handbook(req):
    title = req.GET['title'].strip()
    if title:
        Handbook.objects.create(title=title)
    return HttpResponse('Created')


@permission_required('core.delete_handbook')
def delete_handbook(req):
    book_id = req.GET['book_id']
    hb = Handbook.objects.get(pk=int(book_id))
    hb.delete()
    return HttpResponse('Deleted')


@permission_required('core.can_write_handbook')
def delete_chapter(req):
    chapter_id = req.GET['chapter_id']
    ch = Chapter.objects.get(pk=int(chapter_id))
    ch.delete()
    return HttpResponse('Deleted')
