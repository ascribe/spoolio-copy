# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import deactivate


class EmailTasksTest(TestCase):

    def _sender(self):
        alice, created = User.objects.get_or_create(email='alice@test.com',
                                                    username='alice')
        if created:
            alice.set_password('secret')
            alice.save()
        return alice

    def _receiver(self):
        bob, created = User.objects.get_or_create(email='bob@test.com',
                                                  username='bob')
        if created:
            bob.set_password('secret')
            bob.save()
        return bob

    def _digital_work(self):
        from blobs.models import DigitalWork
        return DigitalWork.objects.create()

    def _piece(self):
        from piece.models import Piece
        alice = self._sender()
        digital_work = self._digital_work()
        return Piece.objects.create(
            user_registered=alice,
            date_created=timezone.now(),
            digital_work=digital_work
        )

    def _edition(self):
        from piece.models import Edition
        alice = self._sender()
        piece = self._piece()
        return Edition.objects.create(
            owner=alice, edition_number=1, parent=piece)

    def test_send_welcome_email(self):
        from ..tasks import send_ascribe_email
        alice = User.objects.create(email='alice@test.com', username='alice')
        alice.set_password('secret')
        alice.save()
        token = 'magictoken'
        send_ascribe_email(
            msg_cls='WelcomeEmailMessage',
            to=alice.email,
            token=token,
            lang='en',
            subdomain='www',
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_send_welcome_email_for_creativecommons_subdomain(self):
        from ..tasks import send_ascribe_email
        alice = User.objects.create(email='alice@test.com', username='alice')
        alice.set_password('secret')
        alice.save()
        token = 'magictoken'
        send_ascribe_email(
            msg_cls='WelcomeEmailMessageCreativeCommons',
            to=alice.email,
            token=token,
            lang='en',
            subdomain='cc',
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Welcome to cc.ascribe.io')

    def test_send_welcome_email_for_23vivi_subdomain(self):
        from ..tasks import send_ascribe_email
        alice = User.objects.create(email='alice@test.com', username='alice')
        alice.set_password('secret')
        alice.save()
        token = 'magictoken'
        send_ascribe_email(
            msg_cls='WelcomeEmailMessage23vivi',
            to=alice.email,
            token=token,
            lang='en',
            subdomain='cc',
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         'Welcome to 23vivi.ascribe.io')

    def test_send_password_reset_email(self):
        from ..tasks import send_ascribe_email
        alice = User.objects.create(email='alice@test.com', username='alice')
        alice.set_password('secret')
        alice.save()
        token = 'magictoken'
        redirect_url = '/password_reset'
        result = send_ascribe_email.delay(
            msg_cls='PasswordResetEmailMessage',
            to=alice.email,
            token=token,
            redirect_url=redirect_url,
            lang='en',
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(len(sent_mail.to), 1)
        self.assertEqual(sent_mail.to[0], alice.email)
        self.assertEqual(sent_mail.from_email, settings.ASCRIBE_EMAIL)
        self.assertEqual(len(sent_mail.alternatives), 1)

    def test_send_share_editions_email(self):
        from ..tasks import send_ascribe_email
        sender = self._sender()
        receiver = self._receiver()
        editions = (self._edition(),)
        message, subdomain = '', 'www'
        result = send_ascribe_email.delay(
            msg_cls='ShareEditionsEmailMessage',
            to=receiver.email,
            sender=sender,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_share_pieces_email(self):
        from ..tasks import send_ascribe_email
        sender = self._sender()
        receiver = self._receiver()
        pieces = (self._piece(),)
        message, subdomain = '', 'www'
        result = send_ascribe_email.delay(
            msg_cls='SharePiecesEmailMessage',
            to=receiver.email,
            sender=sender,
            pieces=pieces,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_email_to_new_owner_on_transfer(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = '', 'www'
        result = send_ascribe_email.delay(
            msg_cls='TransferEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_consignment_request_email_to_consignee(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'on consignment email to consignee', 'www'
        result = send_ascribe_email.delay(
            msg_cls='ConsignRequestReceiverEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_consignor_consignment_info_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'send consignor consignment info email', 'www'
        result = send_ascribe_email.delay(
            msg_cls='ConsignRequestSenderEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_loanee_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'loanee email', 'www'
        result = send_ascribe_email.delay(
            msg_cls='LoanRequestReceiverEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_email_to_loaner(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'loaner email', 'www'
        result = send_ascribe_email.delay(
            msg_cls='LoanRequestSenderEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_consignor_confirmation_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'consignor confirmation', 'www'
        result = send_ascribe_email.delay(
            msg_cls='ConsignConfirmSenderEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_consignor_rejection_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'consignor rejection', 'www'
        result = send_ascribe_email.delay(
            msg_cls='ConsignDenySenderEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_loaner_confirmation_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'loaner confirmation', 'www'
        result = send_ascribe_email.delay(
            msg_cls='LoanConfirmSenderEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_consignor_unconsignment_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'consignor unconsignment', 'www'
        result = send_ascribe_email.delay(
            msg_cls='ConsignTerminateSenderEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_loaner_rejection_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'loaner rejection', 'www'
        result = send_ascribe_email.delay(
            msg_cls='LoanDenySenderEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_consignee_unconsignment_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'consignee unconsignment', 'www'
        result = send_ascribe_email.delay(
            msg_cls='UnconsignmentRequestReceiverEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_loaner_piece_request_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'loaner piece request', 'www'
        result = send_ascribe_email.delay(
            msg_cls='LoanPieceRequestSenderEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_loanee_piece_request_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'loanee piece request', 'www'
        result = send_ascribe_email.delay(
            msg_cls='LoanPieceRequestReceiverEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_consignor_unconsignment_rejection_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        subdomain = 'www'
        result = send_ascribe_email.delay(
            msg_cls='UnconsignmentDenySenderEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_loanee_piece_request_confirmation_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'loanee piece request confirmation', 'www'
        result = send_ascribe_email.delay(
            msg_cls='LoanPieceConfirmReceiverEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_loanee_piece_request_denial_email(self):
        from ..tasks import send_ascribe_email
        sender, receiver = self._sender(), self._receiver()
        editions = (self._edition(),)
        message, subdomain = 'loanee piece request denial', 'www'
        result = send_ascribe_email.delay(
            msg_cls='LoanPieceDenyReceiverEmailMessage',
            sender=sender,
            receiver=receiver,
            editions=editions,
            message=message,
            subdomain=subdomain,
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_loaner_piece_request_denial_email(self):
        from ..tasks import emailOwnerOnDenyLoanPiece
        receiver = self._receiver()
        piece = self._piece()
        subdomain = 'www'
        result = emailOwnerOnDenyLoanPiece.delay(receiver, piece, subdomain)
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_contract_agreement_accepted_email(self):
        from ..tasks import email_contract_agreement_decision
        from blobs.models import OtherData
        from ownership.models import Contract, ContractAgreement
        merlin = User.objects.create(email='merlin@test.com',
                                     username='merlin')
        alice = User.objects.create(email='alice@test.com', username='alice')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(blob=blob, issuer=merlin)
        contract_agreement = ContractAgreement.objects.create(
            contract=contract, signee=alice)
        result = email_contract_agreement_decision.delay(contract_agreement,
                                                         accepted=True)
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_contract_agreement_rejected_email(self):
        from ..tasks import email_contract_agreement_decision
        from blobs.models import OtherData
        from ownership.models import Contract, ContractAgreement
        merlin = User.objects.create(email='merlin@test.com',
                                     username='merlin')
        alice = User.objects.create(email='alice@test.com', username='alice')
        blob = OtherData.objects.create()
        contract = Contract.objects.create(blob=blob, issuer=merlin)
        contract_agreement = ContractAgreement.objects.create(
            contract=contract, signee=alice)
        result = email_contract_agreement_decision.delay(contract_agreement,
                                                         accepted=False)
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_signup_judge_sluice_email(self):
        from ..tasks import email_signup_judge
        from whitelabel.test.util import APIUtilWhitelabel
        alice = User.objects.create(email='alice@test.com', username='alice')
        alice.set_password('secret')
        alice.save()
        APIUtilWhitelabel.create_whitelabel_market(alice, subdomain='sluice')
        token = 'magictoken'
        email_signup_judge(alice, token, subdomain='sluice')
        self.assertEqual(len(mail.outbox), 1)

    def test_send_submit_prize_sluice_email(self):
        from ..tasks import email_submit_prize
        receiver = self._receiver()
        piece = self._piece()
        subdomain = 'sluice'
        result = email_submit_prize.delay(receiver, piece, subdomain)
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)

    def test_send_submit_prize_portfolioreview_email(self):
        from ..tasks import email_submit_prize
        receiver = self._receiver()
        piece = self._piece()
        subdomain = 'portfolioreview'
        result = email_submit_prize.delay(receiver, piece, subdomain)
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)


class EmailLocaleTest(TestCase):
    """
    Some tests to double-check that the translation mechanisms are working,
    when preparing the email contents to send.

    """

    def tearDown(self):
        deactivate()

    @unittest.skip('Refactoring/redesigning emails -- skip for the meantime')
    def test_email_request_reset_password_in_french(self):
        from ..tasks import send_ascribe_email
        from users.models import User
        alice = User.objects.create(
            email='alice@test.com', username='alice')
        alice.set_password('secret')
        alice.save()
        token = 'magictoken'
        redirect_url = '/password_reset'
        result = send_ascribe_email.delay(
            msg_cls='PasswordResetEmailMessage',
            to=alice.email,
            token=token,
            redirect_url=redirect_url,
            lang='fr',
        )
        self.assertIsNone(result.get())
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.subject, 'Réinitialisez votre mot de passe')
        self.assertEqual(len(sent_mail.to), 1)
        self.assertEqual(sent_mail.to[0], alice.email)
        self.assertEqual(sent_mail.from_email, settings.ASCRIBE_EMAIL)
        email_signature = settings.EMAIL_SIGNATURE % {'ascribe_team':
                                                      'L\'équipe ascribe'}
        body = (
            'Bonjour alice, \n\n'
            'Suivez ce lien pour réinitialiser votre mot de passe\n\n'
            '{}?token={}&email={}\n\n -{}'
        ).format(redirect_url, token, alice.email, email_signature)
        self.assertEqual(sent_mail.body, body)
        self.assertEqual(len(sent_mail.alternatives), 1)
        html_message = sent_mail.alternatives[0][0]
        self.assertInHTML('<p>Bonjour alice,</p>', html_message)
        self.assertInHTML(
            '<title>Bienvenue chez ascribe!</title>', html_message)
        self.assertIn(
            ("Vous (ou quelqu'un d'autre) a fait une requête "
             "pour réinitialiser votre mot de passe"),
            html_message
        )
        self.assertIn(
            'Cliquez ici pour réinitialiser votre mot de passe', html_message)

    def test_send_ikono_tv_email_to_contract_signee(self):
        from ..tasks import email_send_contract_agreement
        alice = User.objects.create(
            email='alice@test.com', username='alice')
        email_send_contract_agreement(alice, 'ikonotv')
        self.assertEqual(1, len(mail.outbox))
