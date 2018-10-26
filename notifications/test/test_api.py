from __future__ import absolute_import

from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, force_authenticate


class PieceNotificationEndpointTests(TestCase):

    def test_list(self):
        from acl.models import ActionControl
        from blobs.models import DigitalWork
        from ownership.models import LoanPiece
        from piece.models import Piece
        from ..api import PieceNotificationEndpoint
        from ..models import PieceNotification
        from ..serializers import PieceNotificationSerializer

        alice = User.objects.create(email='alice@xyz.ct', username='alice')
        bob = User.objects.create(email='bob@xyz.ct', username='bob')
        eve = User.objects.create(email='eve@xyz.ct', username='eve')
        digital_work = DigitalWork.objects.create(user=alice)
        alice_piece = Piece.objects.create(
            date_created=datetime.today(),
            user_registered=alice,
            digital_work=digital_work,
            bitcoin_path='btc:alice-path',
            artist_name=alice.username,
            title='rainbow country'
        )
        bob_piece = Piece.objects.create(
            date_created=datetime.today(),
            user_registered=bob,
            digital_work=digital_work,
            bitcoin_path='btc:bob-path',
            artist_name=bob.username,
            title='blue sky'
        )
        ActionControl.objects.create(user=eve, piece=alice_piece, acl_view=True)
        ActionControl.objects.create(user=eve, piece=bob_piece, acl_view=True)
        loan_piece = LoanPiece.objects.create(
            ciphertext_wif='abc',
            piece=alice_piece,
            prev_owner=alice,
            new_owner=eve,
            type=LoanPiece.__name__
        )
        loan_piece = LoanPiece.objects.create(
            ciphertext_wif='abc',
            piece=bob_piece,
            prev_owner=bob,
            new_owner=eve,
            type=LoanPiece.__name__
        )
        url = reverse('api:notifications:piece-list')
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=eve)
        view = PieceNotificationEndpoint.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertIn('notifications', response.data)
        self.assertEqual(len(response.data['notifications']), 2)
        bob_notif = [
            {'action': 'loan',
             'action_str': 'Pending loan request',
             'by': 'bob'}
        ]
        alice_notif = [
            {'action': 'loan',
             'action_str': 'Pending loan request',
             'by': 'alice'}
        ]
        N = []
        for notification in response.data['notifications']:
            self.assertIn('notification', notification)
            self.assertIn('piece', notification)
            N.append(notification['notification'])
        self.assertIn(alice_notif, N)
        self.assertIn(bob_notif, N)
