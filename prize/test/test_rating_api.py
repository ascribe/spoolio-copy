from datetime import datetime, timedelta

import pytz

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import force_authenticate, APIRequestFactory


class RatingEndpointTests(TestCase):

    def test_list_ratings_when_none(self):
        from dynamicfixtures import _prize_juror
        from ..api import RatingEndpoint
        prize_juror = _prize_juror()
        subdomain = prize_juror.prize.whitelabel_settings.subdomain
        url = reverse('api:prize:rating-list',
                      kwargs={'domain_pk': subdomain})
        view = RatingEndpoint.as_view({'get': 'list'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=prize_juror.user)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ratings', response.data)
        self.assertEqual(len(response.data['ratings']), 0)

    def test_list_ratings_when_some(self):
        from dynamicfixtures import (
            _prize_juror,
            _prize_piece_alice,
            _prize_piece_bob,
            _rating_piece_alice,
            _rating_piece_bob,
        )
        from ..api import RatingEndpoint
        _prize_piece_alice()
        _prize_piece_bob()
        rating_piece_alice = _rating_piece_alice()
        rating_piece_bob = _rating_piece_bob()
        prize_juror = _prize_juror()
        subdomain = prize_juror.prize.whitelabel_settings.subdomain
        url = reverse('api:prize:rating-list',
                      kwargs={'domain_pk': subdomain})
        view = RatingEndpoint.as_view({'get': 'list'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=prize_juror.user)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ratings', response.data)
        self.assertEqual(len(response.data['ratings']), 2)
        ratings = [rating['rating'] for rating in response.data['ratings']]
        self.assertIn(str(rating_piece_alice.rating), ratings)
        self.assertIn(str(rating_piece_bob.rating), ratings)

    # TODO HACK ALERT!!! This is a test for a hack!
    def test_list_ratings_for_second_round_of_portfolioreview(self):
        from dynamicfixtures import (
            _prize_juror,
            _prize_piece_alice,
            _prize_piece_bob,
            _rating_piece_alice,
            _rating_piece_bob,
        )
        from ..api import RatingEndpoint
        round_two_starttime = datetime.strptime(
            settings.PORTFOLIO_REVIEW_ROUND_TWO_STARTTIME,
            settings.PORTFOLIO_REVIEW_ROUND_TIMEFORMAT,
        ).replace(tzinfo=pytz.UTC)
        subdomain = 'portfolioreview'
        _prize_piece_alice(subdomain=subdomain)
        _prize_piece_bob(subdomain=subdomain)
        rating_piece_alice = _rating_piece_alice(subdomain=subdomain)
        rating_piece_bob = _rating_piece_bob(subdomain=subdomain)
        rating_piece_alice.datetime = round_two_starttime
        rating_piece_alice.save()
        rating_piece_bob.datetime = round_two_starttime - timedelta(seconds=1)
        rating_piece_bob.save()
        prize_juror = _prize_juror(subdomain=subdomain)
        url = reverse('api:prize:rating-list',
                      kwargs={'domain_pk': subdomain})
        view = RatingEndpoint.as_view({'get': 'list'})
        factory = APIRequestFactory()
        request = factory.get(url, {'prize_round': 2})
        force_authenticate(request, user=prize_juror.user)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ratings', response.data)
        self.assertEqual(len(response.data['ratings']), 1)
        self.assertIn(str(rating_piece_alice.rating),
                      response.data['ratings'][0]['rating'])

    def test_retrieve_rating(self):
        from dynamicfixtures import (
            _prize_juror,
            _prize_piece_alice,
            _rating_piece_alice,
        )
        from ..api import RatingEndpoint
        prize_piece_alice = _prize_piece_alice()
        rating_piece_alice = _rating_piece_alice()
        prize_juror = _prize_juror()
        piece_pk = prize_piece_alice.piece.pk
        subdomain = prize_juror.prize.whitelabel_settings.subdomain
        url = reverse('api:prize:rating-detail',
                      kwargs={'pk': piece_pk, 'domain_pk': subdomain})
        view = RatingEndpoint.as_view({'get': 'retrieve'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=prize_juror.user)
        response = view(request, pk=piece_pk, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating']['rating'],
                         str(rating_piece_alice.rating))

    # TODO HACK ALERT!!! This is a test for a hack!
    def test_retrieve_rating_for_round_two(self):
        from dynamicfixtures import (
            _prize_juror,
            _prize_piece_alice,
            _rating_one_piece_alice,
            _rating_two_piece_alice,
        )
        from ..api import RatingEndpoint
        round_two_starttime = datetime.strptime(
            settings.PORTFOLIO_REVIEW_ROUND_TWO_STARTTIME,
            settings.PORTFOLIO_REVIEW_ROUND_TIMEFORMAT,
        ).replace(tzinfo=pytz.UTC)
        subdomain = 'portfolioreview'
        prize_piece_alice = _prize_piece_alice()
        rating_one = _rating_one_piece_alice(subdomain=subdomain)
        rating_one.datetime = round_two_starttime
        rating_one.save()
        rating_two = _rating_two_piece_alice(subdomain=subdomain)
        rating_two.datetime = round_two_starttime - timedelta(seconds=1)
        rating_two.save()
        prize_juror = _prize_juror(subdomain=subdomain)
        piece_pk = prize_piece_alice.piece.pk
        url = reverse('api:prize:rating-detail',
                      kwargs={'pk': piece_pk, 'domain_pk': subdomain})
        view = RatingEndpoint.as_view({'get': 'retrieve'})
        factory = APIRequestFactory()
        request = factory.get(url, {'prize_round': 2})
        force_authenticate(request, user=prize_juror.user)
        response = view(request, pk=piece_pk, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating']['rating'],
                         str(rating_one.rating))

    def test_retrieve_average_rating(self):
        from dynamicfixtures import (
            _prize_juror,
            _prize_piece_alice,
            _rating_one_piece_alice,
            _rating_two_piece_alice,
        )
        from ..api import RatingEndpoint
        prize_piece_alice = _prize_piece_alice()
        piece = prize_piece_alice.piece
        _rating_one_piece_alice()
        _rating_two_piece_alice()
        prize_juror = _prize_juror()
        subdomain = prize_juror.prize.whitelabel_settings.subdomain
        url = reverse('api:prize:rating-average',
                      kwargs={'pk': piece.pk, 'domain_pk': subdomain})
        view = RatingEndpoint.as_view({'get': 'average'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=prize_juror.user)
        response = view(request, pk=piece.pk, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('selected', response.data['data'])
        self.assertIn('ratings', response.data['data'])
        self.assertIn('average', response.data['data'])
        self.assertEqual(response.data['data']['average'], 4.0)

    # TODO HACK ALERT!!! This is a test for a hack!
    def test_retrieve_average_rating_for_round_two(self):
        from dynamicfixtures import (
            _prize_juror,
            _prize_piece_alice,
            _rating_one_piece_alice,
            _rating_two_piece_alice,
            _rating_three_piece_alice,
        )
        from ..api import RatingEndpoint
        round_two_starttime = datetime.strptime(
            settings.PORTFOLIO_REVIEW_ROUND_TWO_STARTTIME,
            settings.PORTFOLIO_REVIEW_ROUND_TIMEFORMAT,
        ).replace(tzinfo=pytz.UTC)
        subdomain = 'portfolioreview'
        prize_piece_alice = _prize_piece_alice(subdomain=subdomain)
        piece = prize_piece_alice.piece
        rating_one = _rating_one_piece_alice(subdomain=subdomain)
        rating_one.datetime = round_two_starttime
        rating_one.save()
        rating_two = _rating_two_piece_alice(subdomain=subdomain)
        rating_two.datetime = round_two_starttime
        rating_two.save()
        rating_three = _rating_three_piece_alice(subdomain=subdomain)
        rating_three.datetime = round_two_starttime - timedelta(seconds=1)
        rating_three.save()
        prize_juror = _prize_juror(subdomain=subdomain)
        url = reverse('api:prize:rating-average',
                      kwargs={'pk': piece.pk, 'domain_pk': subdomain})
        view = RatingEndpoint.as_view({'get': 'average'})
        factory = APIRequestFactory()
        request = factory.get(url, {'prize_round': 2})
        force_authenticate(request, user=prize_juror.user)
        response = view(request, pk=piece.pk, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('selected', response.data['data'])
        self.assertIn('ratings', response.data['data'])
        self.assertIn('average', response.data['data'])
        self.assertEqual(response.data['data']['average'], 4.0)

    def test_create_rating(self):
        from dynamicfixtures import _prize_juror, _prize_piece_alice
        from ..api import RatingEndpoint
        from ..models import Rating
        self.assertFalse(Rating.objects.exists())
        prize_piece_alice = _prize_piece_alice()
        prize_juror = _prize_juror()
        subdomain = prize_juror.prize.whitelabel_settings.subdomain
        data = {
            'note': 8,
            'piece_id': prize_piece_alice.piece.pk,
        }
        url = reverse('api:prize:rating-list',
                      kwargs={'domain_pk': subdomain})
        view = RatingEndpoint.as_view({'post': 'create'})
        factory = APIRequestFactory()
        request = factory.post(url, data=data)
        force_authenticate(request, user=prize_juror.user)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating']['rating'], '8.0')
        self.assertTrue(Rating.objects.exists())
        self.assertEqual(Rating.objects.get().rating, float(data['note']))

    def test_select_piece(self):
        from dynamicfixtures import (_prize_juror, _prize_piece_alice,
                              _rating_one_piece_alice, _rating_two_piece_alice)
        from ..api import RatingEndpoint
        from ..models import PrizePiece
        prize_piece = _prize_piece_alice()
        self.assertFalse(prize_piece.is_selected)
        piece = prize_piece.piece
        prize_juror = _prize_juror()
        _rating_one_piece_alice()
        _rating_two_piece_alice()
        subdomain = prize_juror.prize.whitelabel_settings.subdomain
        data = {
        }
        url = reverse('api:prize:rating-select',
                      kwargs={'pk': piece.pk, 'domain_pk': subdomain})
        view = RatingEndpoint.as_view({'post': 'select'})
        factory = APIRequestFactory()
        request = factory.post(url, data=data)
        force_authenticate(request, user=prize_juror.user)
        response = view(request, pk=piece.pk, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PrizePiece.objects.get(pk=prize_piece.pk).is_selected)
