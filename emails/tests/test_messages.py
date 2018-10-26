# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from urlparse import urlparse

from django.core import mail
from django.test import TestCase


class OwnershipSenderEmailMessageTests(TestCase):

    def test_subject_with_unicode(self):
        from ..messages import OwnershipSenderEmailMessage
        from dynamicfixtures import _alice, _edition_alice
        alice = _alice()
        edition = _edition_alice()
        edition.parent.title = 'à'
        message = OwnershipSenderEmailMessage(sender=alice,
                                              editions=(edition,))
        message.send()
        self.assertEqual(len(mail.outbox), 1)


class TransferEmailMessageWhitelabelMarketTests(TestCase):

    def test_override_subdomain_23vivi(self):
        from ..messages import TransferEmailMessage23vivi
        from dynamicfixtures import _alice, _bob, _edition_alice
        alice = _alice()
        bob = _bob()
        edition = _edition_alice()
        message = TransferEmailMessage23vivi(sender=alice, receiver=bob,
                                              editions=(edition,), subdomain='23vivi')
        parsed_url = urlparse(message.redirect_url)
        self.assertEqual(parsed_url.netloc.split('.')[0], 'www')

    def test_override_subdomain_lumenus(self):
        from ..messages import TransferEmailMessageLumenus
        from dynamicfixtures import _alice, _bob, _edition_alice
        alice = _alice()
        bob = _bob()
        edition = _edition_alice()
        message = TransferEmailMessageLumenus(sender=alice, receiver=bob,
                                              editions=(edition,), subdomain='lumenus')
        parsed_url = urlparse(message.redirect_url)
        self.assertEqual(parsed_url.netloc.split('.')[0], 'www')
