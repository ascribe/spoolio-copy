from datetime import datetime, timedelta

import pytz

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import force_authenticate, APIRequestFactory


class PrizePieceEndpointTests(TestCase):

    def test_list_pieces_when_none(self):
        from dynamicfixtures import _prize_juror
        from ..api import PrizePieceEndpoint
        prize_juror = _prize_juror()
        subdomain = prize_juror.prize.whitelabel_settings.subdomain
        url = reverse('api:prize:prize-pieces-list',
                      kwargs={'domain_pk': subdomain})
        view = PrizePieceEndpoint.as_view({'get': 'list'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=prize_juror.user)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pieces', response.data)
        self.assertEqual(response.data['count'], 0)

    def test_list_pieces_when_some(self):
        from dynamicfixtures import (
            _djroot_user,
            _prize_juror,
            _prize_piece_alice,
            _prize_piece_bob,
            _rating_piece_alice,
            _rating_piece_bob,
            _alice_bitcoin_wallet,
            _bob_bitcoin_wallet,
        )
        from ..api import PrizePieceEndpoint
        _djroot_user()
        _prize_piece_alice()
        _prize_piece_bob()
        _rating_piece_alice()
        _rating_piece_bob()
        prize_juror = _prize_juror()
        _alice_bitcoin_wallet()
        _bob_bitcoin_wallet()
        subdomain = prize_juror.prize.whitelabel_settings.subdomain
        url = reverse('api:prize:prize-pieces-list',
                      kwargs={'domain_pk': subdomain})
        view = PrizePieceEndpoint.as_view({'get': 'list'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=prize_juror.user)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    # TODO HACK ALERT!!! This is a test for a hack!
    def test_list_pieces_for_second_round_of_portfolioreview(self):
        from dynamicfixtures import (
            _djroot_user,
            _prize_juror,
            _prize_piece_alice,
            _prize_piece_bob,
            _rating_piece_alice,
            _rating_piece_bob,
            _alice_bitcoin_wallet,
            _bob_bitcoin_wallet,
        )
        from ..api import PrizePieceEndpoint
        _djroot_user()
        _alice_bitcoin_wallet()
        _bob_bitcoin_wallet()
        subdomain = 'portfolioreview'
        prize_piece_alice = _prize_piece_alice(subdomain=subdomain)
        prize_piece_alice.round = 2
        prize_piece_alice.save()
        _prize_piece_bob(subdomain=subdomain)
        round_two_starttime = datetime.strptime(
            settings.PORTFOLIO_REVIEW_ROUND_TWO_STARTTIME,
            settings.PORTFOLIO_REVIEW_ROUND_TIMEFORMAT,
        ).replace(tzinfo=pytz.UTC)
        rating_piece_alice = _rating_piece_alice(subdomain=subdomain)
        rating_piece_bob = _rating_piece_bob(subdomain=subdomain)
        rating_piece_alice.datetime = round_two_starttime
        rating_piece_alice.save()
        rating_piece_bob.datetime = round_two_starttime - timedelta(seconds=1)
        rating_piece_bob.save()
        prize_juror = _prize_juror(subdomain=subdomain)
        prize = prize_juror.prize
        prize.active_round = 2
        prize.save()
        url = reverse('api:prize:prize-pieces-list',
                      kwargs={'domain_pk': subdomain})
        view = PrizePieceEndpoint.as_view({'get': 'list'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=prize_juror.user)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIsNotNone(response.data['pieces'][0]['ratings'])

    def test_create_prize_piece(self):
        from dynamicfixtures import (
            _djroot_user,
            _djroot_bitcoin_wallet,
            _alice,
            _alice_bitcoin_wallet,
            _license,
            _digital_work_alice,
            _prize_with_whitelabel,
        )
        from ..api import PrizePieceEndpoint
        subdomain = 'portfolioreview'
        _djroot_user()
        _djroot_bitcoin_wallet()
        alice = _alice()
        _alice_bitcoin_wallet()
        license = _license()
        digital_work = _digital_work_alice()
        _prize_with_whitelabel(subdomain=subdomain)
        data = {
            'prize_name': subdomain,
            'terms': True,
            'digital_work_key': digital_work.key,
            'artist_name': 'alice',
            'title': 'green stars',
            'license': license.code,
        }
        url = reverse('api:prize:prize-pieces-list',
                      kwargs={'domain_pk': subdomain})
        view = PrizePieceEndpoint.as_view({'post': 'create'})
        factory = APIRequestFactory()
        headers = {
            'HTTP_ORIGIN': 'http://{}.ascribe.test'.format(subdomain),
        }
        request = factory.post(url, data=data, **headers)
        force_authenticate(request, user=alice)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
