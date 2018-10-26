from __future__ import absolute_import

import os
from datetime import datetime, timedelta

from django.conf import settings

from rest_framework.test import APIRequestFactory

import pytest

from blobs.test.util import APIUtilDigitalWork, APIUtilThumbnail
from ownership.models import OwnershipTransfer, Consignment, Loan, LoanPiece, Share, SharePiece
from ownership.test.util import APIUtilTransfer, APIUtilConsign, APIUtilLoanEdition, APIUtilLoanPiece, \
    APIUtilShareEdition, APIUtilSharePiece
from piece.test.util import APIUtilPiece
from s3.test.mocks import MockAwsTestCase
from users.test.util import APIUtilUsers
from webhooks.test.util import APIUtilWebhook


@pytest.mark.skipif(
    os.environ.get('TRAVIS') == 'true',
    reason=('random failure, and slowing down ci phase,as we'
            'need to relaunch all tests each time it fails')
)
# Test webhook inheritance
class ConsignWebhookTest(MockAwsTestCase,
                         APIUtilConsign,
                         APIUtilUsers,
                         APIUtilDigitalWork,
                         APIUtilThumbnail,
                         APIUtilPiece,
                         APIUtilWebhook):
    fixtures = ['licenses.json']

    def setUp(self):
        super(ConsignWebhookTest, self).setUp()
        self.password = '0' * 10
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digitalwork_web = self.create_digitalwork(self.web_user)
        self.thumbnail_web = self.create_thumbnail(self.web_user)
        self.piece_web, self.editions_web = self.create_piece(self.web_user, self.digitalwork_web,
                                                              self.thumbnail_web, num_editions=10)
        self.piece_other, self.editions_other = self.create_piece(self.other_user, self.digitalwork_web,
                                                                  self.thumbnail_web, num_editions=10)
        self.webhook_web = self.create_webhook(self.web_user, 'webhook.consign', 'http://localhost.com/')
        self.factory = APIRequestFactory()

    def test_webhook_inheritance(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        self.create_consign(self.web_user,
                            self.other_user.email,
                            self.editions_web[0].bitcoin_id,
                            self.password)
        consignment_db = Consignment.objects.get(edition_id=self.editions_web[0].id)
        self.assertEqual(consignment_db.webhook_event, 'consign.webhook')
        self.assertEqual(len(consignment_db.webhook_data), 7)


# Test webhook inheritance
class TransferWebhookTest(MockAwsTestCase,
                          APIUtilTransfer,
                          APIUtilUsers,
                          APIUtilDigitalWork,
                          APIUtilThumbnail,
                          APIUtilPiece,
                          APIUtilWebhook):
    fixtures = ['licenses.json']

    def setUp(self):
        super(TransferWebhookTest, self).setUp()
        self.password = '0' * 10
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digitalwork_web = self.create_digitalwork(self.web_user)
        self.thumbnail_web = self.create_thumbnail(self.web_user)
        self.piece_web, self.editions_web = self.create_piece(self.web_user, self.digitalwork_web,
                                                              self.thumbnail_web, num_editions=10)
        self.piece_other, self.editions_other = self.create_piece(self.other_user, self.digitalwork_web,
                                                                  self.thumbnail_web, num_editions=10)
        self.webhook_web = self.create_webhook(self.web_user, 'webhook.transfer', 'http://localhost.com/')
        self.factory = APIRequestFactory()

    def test_webhook_inheritance(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        bitcoin_id = self.editions_web[0].bitcoin_id
        edition_id = self.editions_web[0].id
        self.create_transfer(self.web_user, self.other_user.email, bitcoin_id, self.password)
        transfer_db = OwnershipTransfer.objects.get(edition_id=edition_id)
        self.assertEqual(transfer_db.webhook_event, 'transfer.webhook')
        self.assertEqual(len(transfer_db.webhook_data), 5)


# Test webhook inheritance
class LoanEditionWebhookTest(MockAwsTestCase,
                             APIUtilLoanEdition,
                             APIUtilUsers,
                             APIUtilDigitalWork,
                             APIUtilThumbnail,
                             APIUtilPiece,
                             APIUtilWebhook):
    fixtures = ['licenses.json']

    def setUp(self):
        super(LoanEditionWebhookTest, self).setUp()
        self.password = '0' * 10
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digitalwork_web = self.create_digitalwork(self.web_user)
        self.thumbnail_web = self.create_thumbnail(self.web_user)
        self.piece_web, self.editions_web = self.create_piece(self.web_user, self.digitalwork_web,
                                                              self.thumbnail_web, num_editions=10)
        self.piece_other, self.editions_other = self.create_piece(self.other_user, self.digitalwork_web,
                                                                  self.thumbnail_web, num_editions=10)
        self.webhook_web = self.create_webhook(self.web_user, 'webhook.loan', 'http://localhost.com/')
        self.factory = APIRequestFactory()

    def test_webhook_inheritance(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        bitcoin_id = self.editions_web[0].bitcoin_id
        edition_id = self.editions_web[0].id
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)

        self.create_loan_edition(self.web_user, self.other_user.email, bitcoin_id, startdate, enddate, self.password)
        loan_db = Loan.objects.get(edition_id=edition_id)
        self.assertEqual(loan_db.webhook_event, 'loan.webhook')
        self.assertEqual(len(loan_db.webhook_data), 7)


# Test webhook inheritance
class LoanPieceWebhookTest(MockAwsTestCase,
                           APIUtilLoanPiece,
                           APIUtilUsers,
                           APIUtilDigitalWork,
                           APIUtilThumbnail,
                           APIUtilPiece,
                           APIUtilWebhook):
    fixtures = ['licenses.json']

    def setUp(self):
        super(LoanPieceWebhookTest, self).setUp()
        self.password = '0' * 10
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digitalwork_web = self.create_digitalwork(self.web_user)
        self.thumbnail_web = self.create_thumbnail(self.web_user)
        self.piece_web, self.editions_web = self.create_piece(self.web_user, self.digitalwork_web,
                                                              self.thumbnail_web, num_editions=10)
        self.piece_other, self.editions_other = self.create_piece(self.other_user, self.digitalwork_web,
                                                                  self.thumbnail_web, num_editions=10)
        self.webhook_web = self.create_webhook(self.web_user, 'webhook.loan', 'http://localhost.com/')
        self.factory = APIRequestFactory()

    def test_webhook_inheritance(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        piece_id = self.piece_web.id
        startdate = datetime.utcnow().date()
        enddate = datetime.utcnow().date() + timedelta(days=1)

        self.create_loan_piece(self.web_user, self.other_user.email, piece_id, startdate, enddate, self.password)
        loan_db = LoanPiece.objects.get(piece_id=piece_id)
        self.assertEqual(loan_db.webhook_event, 'loan.webhook')
        self.assertEqual(len(loan_db.webhook_data), 7)


# Test webhook inheritance
class ShareEditionWebhookTest(MockAwsTestCase,
                              APIUtilShareEdition,
                              APIUtilUsers,
                              APIUtilDigitalWork,
                              APIUtilThumbnail,
                              APIUtilPiece,
                              APIUtilWebhook):
    fixtures = ['licenses.json']

    def setUp(self):
        super(ShareEditionWebhookTest, self).setUp()
        self.password = '0' * 10
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digitalwork_web = self.create_digitalwork(self.web_user)
        self.thumbnail_web = self.create_thumbnail(self.web_user)
        self.piece_web, self.editions_web = self.create_piece(self.web_user, self.digitalwork_web,
                                                              self.thumbnail_web, num_editions=10)
        self.piece_other, self.editions_other = self.create_piece(self.other_user, self.digitalwork_web,
                                                                  self.thumbnail_web, num_editions=10)
        self.webhook_web = self.create_webhook(self.web_user, 'webhook.share', 'http://localhost.com/')
        self.factory = APIRequestFactory()

    def test_webhook_inheritance(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        bitcoin_id = self.editions_web[0].bitcoin_id
        edition_id = self.editions_web[0].id

        self.create_share_edition(self.web_user, self.other_user.email, bitcoin_id)
        share_db = Share.objects.get(edition_id=edition_id)
        self.assertEqual(share_db.webhook_event, 'share.webhook')
        self.assertEqual(len(share_db.webhook_data), 5)


# Test webhook inheritance
class SharePieceWebhookTest(MockAwsTestCase,
                            APIUtilSharePiece,
                            APIUtilUsers,
                            APIUtilDigitalWork,
                            APIUtilThumbnail,
                            APIUtilPiece,
                            APIUtilWebhook):
    fixtures = ['licenses.json']

    def setUp(self):
        super(SharePieceWebhookTest, self).setUp()
        self.password = '0' * 10
        self.admin_user = self.create_user('mysite_user', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.web_user = self.create_user('web-user@test.com')
        self.other_user = self.create_user('other-user@test.com')
        self.digitalwork_web = self.create_digitalwork(self.web_user)
        self.thumbnail_web = self.create_thumbnail(self.web_user)
        self.piece_web, self.editions_web = self.create_piece(self.web_user, self.digitalwork_web,
                                                              self.thumbnail_web, num_editions=10)
        self.piece_other, self.editions_other = self.create_piece(self.other_user, self.digitalwork_web,
                                                                  self.thumbnail_web, num_editions=10)
        self.webhook_web = self.create_webhook(self.web_user, 'webhook.share', 'http://localhost.com/')
        self.factory = APIRequestFactory()

    def test_webhook_inheritance(self):
        """
        Test that a web user can only see himself.
        He should not have access to the other users in the db.
        """
        piece_id = self.piece_web.id

        self.create_share_piece(self.web_user, self.other_user.email, piece_id)
        share_db = SharePiece.objects.get(piece_id=piece_id)
        self.assertEqual(share_db.webhook_event, 'share.webhook')
        self.assertEqual(len(share_db.webhook_data), 5)
