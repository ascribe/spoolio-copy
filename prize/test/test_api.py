from __future__ import absolute_import

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.test import force_authenticate, APIRequestFactory

from blobs.test.util import APIUtilDigitalWork, APIUtilThumbnail
from piece.test.util import APIUtilPiece
from prize.api import PrizeEndpoint
from prize.test.util import APIUtilPrize
from users.test.util import APIUtilUsers
from whitelabel.test.util import APIUtilWhitelabel


class PrizeEndpointTest(TestCase,
                        APIUtilUsers,
                        APIUtilDigitalWork,
                        APIUtilThumbnail,
                        APIUtilPiece,
                        APIUtilPrize,
                        APIUtilWhitelabel):
    def setUp(self):
        self.password = '0' * 10

        self.user_admin = self.create_user('admin@test.com', password=settings.DJANGO_PYCOIN_ADMIN_PASS)
        self.user1 = self.create_user('user@test.com')

        self.whitelabel = []
        self.whitelabel.append(self.create_whitelabel_market(self.user_admin, subdomain='prize1'))
        self.whitelabel.append(self.create_whitelabel_market(self.user1, subdomain='prize2'))
        self.whitelabel.append(self.create_whitelabel_market(self.user1, subdomain='prize3'))

        self.prizes = []
        self.prizes.append(self.create_prize(self.user_admin, self.whitelabel[0]))
        self.prizes.append(self.create_prize(self.user1, self.whitelabel[1]))
        self.prizes.append(self.create_prize(self.user1, self.whitelabel[2]))
        self.digitalwork_user1 = self.create_digitalwork(self.user1)
        self.thumbnail_user1 = self.create_thumbnail(self.user1)

        self.factory = APIRequestFactory()

    def test_list_web(self):
        """
        Test that a web user can only see all prizes
        """
        # signup & activate user3
        view = PrizeEndpoint.as_view({'get': 'list'})
        url = '/api/prizes/'
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request)

        self.assertIs(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_retrieve_web(self):
        """
        Test that a web user can see all prizes
        """
        # signup & activate user3
        view = PrizeEndpoint.as_view({'get': 'retrieve'})
        url = '/api/prizes/'
        request = self.factory.get(url)

        force_authenticate(request, user=self.user1)

        response = view(request, pk=self.prizes[1].data['prize']['subdomain'])

        self.assertIs(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subdomain'], self.prizes[1].data['prize']['subdomain'])

        response = view(request, pk=self.prizes[0].data['prize']['subdomain'])

        self.assertIs(response.status_code, status.HTTP_200_OK)


class PrizeApiTests(TestCase):

    def test_list_prizes(self):
        from ..api import PrizeEndpoint
        from dynamicfixtures import _alice, _prize_with_whitelabel
        alice = _alice()
        _prize_with_whitelabel(subdomain='yellow')
        _prize_with_whitelabel(subdomain='green')
        url = reverse('api:prize:prize-list')
        view = PrizeEndpoint.as_view({'get': 'list'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        subdomains = [prize['subdomain'] for prize in response.data['results']]
        self.assertIn('yellow', subdomains)
        self.assertIn('green', subdomains)

    def test_retrieve_prize(self):
        from ..api import PrizeEndpoint
        from dynamicfixtures import _alice, _prize_with_whitelabel
        alice = _alice()
        prize = _prize_with_whitelabel(subdomain='yellow')
        url = reverse('api:prize:prize-detail',
                      kwargs={'pk': prize.subdomain})
        view = PrizeEndpoint.as_view({'get': 'retrieve'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=alice)
        response = view(request, pk=prize.subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('active_round', response.data)
        self.assertIn('name', response.data)
        self.assertIn('whitelabel_settings', response.data)
        self.assertIn('rounds', response.data)
        self.assertIn('active', response.data)
        self.assertIn('subdomain', response.data)
        self.assertIn('num_submissions', response.data)
        self.assertEqual(response.data['active_round'], prize.active_round)
        self.assertEqual(response.data['name'], prize.name)
        self.assertEqual(response.data['whitelabel_settings'],
                         prize.whitelabel_settings.pk)
        self.assertEqual(response.data['rounds'], prize.rounds)
        self.assertEqual(response.data['active'], prize.active)
        self.assertEqual(response.data['subdomain'], prize.subdomain)
        self.assertEqual(response.data['num_submissions'],
                         prize.num_submissions)

    def test_update_prize_with_new_round(self):
        from ..api import PrizeEndpoint
        from ..models import Prize, PrizeUser
        from dynamicfixtures import (
            _alice, _prize_with_whitelabel, _prize_judge, _prize_juror)
        alice = _alice()
        prize = _prize_with_whitelabel(subdomain='yellow')
        prize.rounds = 3
        prize.save()
        judge = _prize_judge(subdomain='yellow')
        juror = _prize_juror(subdomain='yellow')
        data = {
            'active_round': 2,
            'name': 'yellow',
            'rounds': 3,
            'active': False,
            'subdomain': 'yellow',
            'num_submissions': None,
        }
        url = reverse('api:prize:prize-detail',
                      kwargs={'pk': prize.pk})
        view = PrizeEndpoint.as_view({'put': 'update'})
        factory = APIRequestFactory()
        request = factory.put(url, data=data, format='json')
        force_authenticate(request, user=alice)
        self.assertEqual(prize.active_round, 1)
        self.assertTrue(judge.is_judge)
        self.assertTrue(juror.is_jury)
        response = view(request, pk=prize.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['active_round'], 2)
        self.assertEqual(Prize.objects.get(pk=prize.pk).active_round, 2)
        judge = PrizeUser.objects.get(pk=judge.pk)
        self.assertFalse(judge.is_judge)
        self.assertFalse(judge.is_jury)
        juror = PrizeUser.objects.get(pk=juror.pk)
        self.assertFalse(juror.is_jury)
        self.assertFalse(juror.is_judge)
