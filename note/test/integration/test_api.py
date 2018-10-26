from django.conf import settings

from rest_framework import status

from .util import APINoteUtil
from ..models import Note
from blobs.test.util import APIUtilDigitalWork, APIUtilThumbnail
from piece.test.util import APIUtilPiece
from s3.test.mocks import MockAwsTestCase
from users.test.util import APIUtilUsers


class NoteEndpointTest(MockAwsTestCase, APIUtilUsers, APIUtilDigitalWork,
                       APIUtilThumbnail, APIUtilPiece, APINoteUtil):
    fixtures = ['licenses.json']

    def setUp(self):
        super(NoteEndpointTest, self).setUp()
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user1@test.com')
        self.user2 = self.create_user('user2@test.com')

        self.digitalwok_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.piece_user1, self.editions_user1 = self.create_piece(self.user1,
                                                                  self.digitalwok_user1,
                                                                  self.thumbnail_user1,
                                                                  num_editions=2)
        Note.objects.all().delete()

    def testCreatePublicEditionNote(self):
        # test create
        edition = self.editions_user1[0]
        response = self.create_edition_public_note(self.user1, edition.bitcoin_id, 'Public Edition Note')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def testCreatePrivateEditionNote(self):
        edition = self.editions_user1[0]
        response = self.create_edition_private_note(self.user1, edition.bitcoin_id, 'Private Edition Note')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def testListPublicEditionNote(self):
        # create note
        edition = self.editions_user1[0]
        self.create_edition_public_note(self.user1, edition.bitcoin_id, 'Public Edition Note')

        # list
        response = self.list_edition_public_note(self.user1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check content
        note = response.data['edition_notes'][0]['note']
        success = response.data['success']
        self.assertEqual(note, u'Public Edition Note')
        self.assertTrue(success)

    def testListPrivateEditionNote(self):
        # create note
        edition = self.editions_user1[0]
        self.create_edition_private_note(self.user1, edition.bitcoin_id, 'Private Edition Note')

        # list
        response = self.list_edition_private_note(self.user1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check content
        note = response.data['notes'][0]['note']
        success = response.data['success']
        self.assertEqual(note, u'Private Edition Note')
        self.assertTrue(success)

    def testCreatePublicPieceNote(self):
        piece = self.piece_user1
        response = self.create_piece_public_note(self.user1, piece.id, 'Public Piece Note')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def testCreatePrivatePieceNote(self):
        piece = self.piece_user1
        response = self.create_piece_private_note(self.user1, piece.id, 'Private Piece Note')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def testListPublicPieceNote(self):
        # create note
        piece = self.piece_user1
        self.create_piece_public_note(self.user1, piece.id, 'Public Piece Note')

        # list
        response = self.list_piece_public_note(self.user1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check content
        note = response.data['piece_notes'][0]['note']
        success = response.data['success']
        self.assertEqual(note, u'Public Piece Note')
        self.assertTrue(success)

    def testListPrivatePieceNote(self):
        # create note
        piece = self.piece_user1
        self.create_piece_private_note(self.user1, piece.id, 'Private Piece Note')

        # list
        response = self.list_piece_private_note(self.user1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check content
        note = response.data['notes'][0]['note']
        success = response.data['success']
        self.assertEqual(note, u'Private Piece Note')
        self.assertTrue(success)
