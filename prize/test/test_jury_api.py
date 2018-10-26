import unittest

from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import force_authenticate, APIRequestFactory


class JuryEndpointTests(TestCase):

    def _admin(self):
        return User.objects.create(username='admin', email='admin@cos.mos')

    def test_list_jury(self):
        from dynamicfixtures import _prize_with_whitelabel
        from ..api import PrizeJuryEndpoint
        from ..models import PrizeUser
        admin = self._admin()
        juria = User.objects.create(username='juria', email='juria@kos.mo')
        jurio = User.objects.create(username='jurio', email='jurio@kos.mo')
        prize = _prize_with_whitelabel()
        subdomain = prize.whitelabel_settings.subdomain
        PrizeUser.objects.create(user=admin, prize=prize, is_admin=True)
        PrizeUser.objects.create(user=juria, prize=prize, is_jury=True)
        PrizeUser.objects.create(user=jurio, prize=prize, is_jury=True)
        url = reverse('api:prize:prize-jury-list',
                      kwargs={'domain_pk': subdomain})
        view = PrizeJuryEndpoint.as_view({'get': 'list'})
        factory = APIRequestFactory()
        request = factory.get(url)
        force_authenticate(request, user=admin)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('members', response.data)
        jury = response.data['members']
        self.assertEqual(len(jury), 2)
        jury_usernames = (member['username'] for member in jury)
        self.assertTrue('juria' in jury_usernames)
        self.assertTrue('jurio' in jury_usernames)

    def test_create_jury_for_non_existing_user(self):
        from dynamicfixtures import _prize_with_whitelabel
        from ..api import PrizeJuryEndpoint
        from ..models import PrizeUser
        new_jury_member_email = 'juri@kos.mo'
        admin = self._admin()
        prize = _prize_with_whitelabel()
        PrizeUser.objects.create(user=admin, prize=prize, is_admin=True)
        subdomain = prize.whitelabel_settings.subdomain
        url = reverse('api:prize:prize-jury-list',
                      kwargs={'domain_pk': subdomain})
        view = PrizeJuryEndpoint.as_view({'post': 'create'})
        factory = APIRequestFactory()
        request = factory.post(url, data={'email': new_jury_member_email})
        force_authenticate(request, user=admin)
        response = view(request, domain_pk=subdomain)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_jury_member = User.objects.get(email=new_jury_member_email)
        prize_new_jury_member = PrizeUser.objects.get(prize=prize,
                                                      user=new_jury_member)
        self.assertTrue(prize_new_jury_member.is_jury)
        roles = [role['type'] for role in
                 new_jury_member.role_at_user.values('type')]
        self.assertEqual(len(roles), 2)
        self.assertIn('UserNeedsToRegisterRole', roles)
        self.assertIn('UserValidateEmailRole', roles)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'Invitation to judge for {}.'.format(
                prize.whitelabel_settings.name),
        )

    # TODO
    @unittest.skip('todo')
    def test_create_jury_for_existing_user(self):
        raise NotImplementedError
