import unittest

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone
from django.utils.six import StringIO


@unittest.skip('wip')
class PreviewMailsCommandTests(TestCase):

    def _alice(self):
        alice, created = User.objects.get_or_create(email='alice@test.com',
                                                    username='alice')
        if created:
            alice.set_password('secret')
            alice.save()
        return alice

    def _bob(self):
        return User.objects.create(email='bob@test.com')

    def _digital_work(self):
        from blobs.models import DigitalWork
        return DigitalWork.objects.create()

    def _piece(self):
        from piece.models import Piece
        alice = self._alice()
        digital_work = self._digital_work()
        return Piece.objects.create(
            user_registered=alice,
            date_created=timezone.now(),
            digital_work=digital_work
        )

    def test_signup(self):
        alice = self._alice()
        out = StringIO()
        call_command('previewmails', 'signup', to=alice.email, out=out)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Welcome to ascribe')
        # self.assertEqual(
        #    Successfully sent email "signup"\n', out.getvalue())

    def test_password_reset(self):
        from emails.messages import PasswordResetEmailMessage
        alice = self._alice()
        out = StringIO()
        call_command('previewmails', 'password_reset', to=alice.email, out=out)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         PasswordResetEmailMessage.SUBJECT)
        # self.assertEqual(
        #    'Successfully sent email "signup"\n', out.getvalue())

    def test_share(self):
        # from emails.messages import PasswordResetEmailMessage
        alice, bob = self._alice(), self._bob()
        digiwork = self._piece()
        out = StringIO()
        call_command(
            'previewmails',
            'share',
            from_email=alice.email,
            to=bob.email,
            digiworks=digiwork,
            out=out
        )
        self.assertEqual(len(mail.outbox), 1)
        #self.assertEqual(mail.outbox[0].subject,
        #                 PasswordResetEmailMessage.SUBJECT)
        # self.assertEqual(
        #    'Successfully sent email "signup"\n', out.getvalue())

    def test_with_many_mail(self):
        alice = self._alice()
        out = StringIO()
        call_command(
            'previewmails',
            'signup',
            'password_reset',
            to=alice.email,
            stdout=out
        )
        self.assertIn('Successfully sent email "signup"\n', out.getvalue())
        self.assertIn(
            'Successfully sent email "password_reset"\n', out.getvalue())

    @unittest.skip('temporary')
    def test_without_mails(self):
        """
        This should send all mails, contained in ``CHOICES``.

        """
        alice = self._alice()
        out = StringIO()
        call_command('previewmails', to=alice.email, stdout=out)
        self.assertIn('Successfully sent email "signup"\n', out.getvalue())
        self.assertIn(
            'Successfully sent email "password_reset"\n', out.getvalue())

    def test_with_invalid_mail(self):
        from ..management.commands.previewmails import CHOICES
        out = StringIO()
        with self.assertRaises(CommandError) as cm:
            call_command('previewmails', 'non-existant-mail', stdout=out)
        self.assertEqual(
            cm.exception.message,
            ("Error: argument mails: invalid choice: 'non-existant-mail' "
             "(choose from {})".format(', '.join((repr(c) for c in CHOICES))))
        )
