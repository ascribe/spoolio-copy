from django.conf import settings
from django.test import TestCase
from django.utils.datetime_safe import datetime

from prize.models import Rating, Prize, PrizePiece
from piece.test.util import APIUtilPiece
from users.test.util import APIUtilUsers
from blobs.test.util import APIUtilThumbnail, APIUtilDigitalWork
from s3.test.mocks import MockAwsTestCase
from whitelabel.test.util import APIUtilWhitelabel

__author__ = 'dimi'


class PrizeTestCase(TestCase, APIUtilUsers):
    def setUp(self):
        """
        generate user data
        """
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')

    def testCreatePrize(self):
        prize_whitelabel = APIUtilWhitelabel.create_whitelabel_market(self.user1, subdomain='TESTPRIZE')
        save_prize = Prize(whitelabel_settings=prize_whitelabel,
                           rounds=2,
                           active_round=1,
                           active=True)

        save_prize.save()
        find_prize = Prize.objects.get(whitelabel_settings__name=save_prize.name)
        self.assertTrue(save_prize == find_prize)


class PrizePieceTestCase(MockAwsTestCase,
                         APIUtilUsers,
                         APIUtilPiece,
                         APIUtilThumbnail,
                         APIUtilDigitalWork):
    fixtures = ['licenses.json']

    def setUp(self):
        """
        generate user data
        """
        super(PrizePieceTestCase, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=0)
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

    def testCreatePieceAtPrize(self):
        prize_whitelabel = APIUtilWhitelabel.create_whitelabel_market(self.user1, subdomain='TESTPRIZE')
        save_prize = Prize(whitelabel_settings=prize_whitelabel,
                           rounds=2,
                           active_round=1,
                           active=True)
        save_prize.save()

        save_prize_piece = PrizePiece(user=self.user1, piece=self.piece_user1, prize=save_prize,
                                      extra_data={'extra_data_string': 'something'})
        save_prize_piece.save()

        find_prize_piece = PrizePiece.objects.get(id=save_prize_piece.id)
        self.assertTrue(save_prize_piece, find_prize_piece)

    def testUpdatePrize(self):
        prize_whitelabel = APIUtilWhitelabel.create_whitelabel_market(self.user1, subdomain='TESTPRIZE')
        save_prize = Prize(whitelabel_settings=prize_whitelabel,
                           rounds=2,
                           active_round=1,
                           active=True)
        save_prize.save()

        save_prize_piece = PrizePiece(user=self.user1, piece=self.piece_user1, prize=save_prize,
                                      extra_data={'extra_data_string': 'something'})
        save_prize_piece.save()

        save_prize_piece.extra_data = {'extra_data_string': 'something else', 'something else': 'blabla'}
        save_prize_piece.save()

        find_prize_piece = PrizePiece.objects.get(id=save_prize_piece.id)
        self.assertTrue(save_prize_piece == find_prize_piece)
        self.assertEqual(find_prize_piece.extra_data,
                         str({'extra_data_string': 'something else', 'something else': 'blabla'}))


class RatingTestCase(MockAwsTestCase,
                     APIUtilUsers,
                     APIUtilDigitalWork,
                     APIUtilThumbnail,
                     APIUtilPiece):
    fixtures = ['licenses.json']

    def setUp(self):
        """
        generate user data
        """
        super(RatingTestCase, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=0)

    def testCreateRating(self):
        user = self.user_admin

        save_note = Rating(user=user,
                           piece=self.piece_user1,
                           edition=None,
                           note=8,
                           type=Rating.__name__)
        save_note.save()

        find_note = Rating.objects.get(id=save_note.id)
        self.assertTrue(save_note == find_note)
        self.assertEqual(find_note.rating, 8)

    def testUpdateRating(self):
        user = self.user_admin

        save_note = Rating(user=user,
                           piece=self.piece_user1,
                           edition=None,
                           note=10,
                           type=Rating.__name__)
        save_note.save()

        save_note.rating = 99
        save_note.save()

        find_note = Rating.objects.get(id=save_note.id)
        self.assertTrue(save_note == find_note)
        self.assertEqual(find_note.rating, 99)
