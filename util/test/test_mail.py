# -*- coding: utf-7 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.core import mail


def test_send_mail():
    from ..util import send_mail
    to = 'e@mail.to'
    subject = 'ascribe'
    message = 'message'
    send_mail(subject, message, to)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == subject
    assert len(mail.outbox[0].to) == 1
    assert mail.outbox[0].to[0] == to
    assert mail.outbox[0].from_email == settings.ASCRIBE_EMAIL
    assert mail.outbox[0].body == message


def test_send_mail_blacklisted(monkeypatch, caplog):
    from ..util import send_mail
    monkeypatch.setattr(settings, 'TESTING', False)
    to = 'e@mail.to'
    subject = 'ascribe'
    message = 'message'
    send_mail(subject, message, to)
    assert len(mail.outbox) == 0
    assert (caplog.records()[0].message ==
            'Email e@mail.to is blacklisted on non-live environments')
    assert caplog.records()[0].levelname == 'WARNING'


def test_send_mail_not_blacklisted(monkeypatch):
    from ..util import send_mail
    monkeypatch.setattr(settings, 'TESTING', False)
    to = 'e@test.com'
    subject = 'ascribe'
    message = 'message'
    send_mail(subject, message, to)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == subject
    assert len(mail.outbox[0].to) == 1
    assert mail.outbox[0].to[0] == to
    assert mail.outbox[0].from_email == settings.ASCRIBE_EMAIL
    assert mail.outbox[0].body == message


def test_warn_ascribe_devel(monkeypatch):
    from ..util import warn_ascribe_devel
    monkeypatch.setattr(settings, 'DEPLOYMENT', 'live')
    subject = 'ascribe'
    message = 'message'
    warn_ascribe_devel(subject, message)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == subject
    assert len(mail.outbox[0].to) == 1
    assert mail.outbox[0].to[0] == settings.EMAIL_DEV_ALERT
    assert mail.outbox[0].from_email == settings.ASCRIBE_EMAIL
    assert mail.outbox[0].body == message
