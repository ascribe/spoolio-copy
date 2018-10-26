from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework import status
from rest_framework.serializers import ValidationError


class PrizeSerializerValidatorTests(TestCase):
    """
    Tests validators used throughout the prize-related serializer.

    """
    def test_validate_non_existing_prize(self):
        from ..serializers import _validate_prize
        alice = User.objects.create(email='alice@test.com', username='alice')
        with self.assertRaises(ValidationError) as cm:
            _validate_prize('cosmic', alice)
        exception = cm.exception
        self.assertEqual(exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(exception.detail), 1)
        self.assertEqual(exception.detail[0],
                         'The prize cosmic does not exist')

    def test_validate_non_active_prize(self):
        from ..models import Prize
        from ..serializers import _validate_prize
        from whitelabel.test.util import APIUtilWhitelabel
        alice = User.objects.create(email='alice@test.com', username='alice')
        cosmic_whitelabel = APIUtilWhitelabel.create_whitelabel_market(alice, subdomain='cosmic')
        cosmic_prize = Prize(whitelabel_settings=cosmic_whitelabel, active=False)
        cosmic_prize.save()
        with self.assertRaises(ValidationError) as cm:
            _validate_prize(cosmic_prize.subdomain, alice)
        exception = cm.exception
        self.assertEqual(exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(exception.detail), 1)
        self.assertEqual(exception.detail[0], 'The prize cosmic is not active')

    def test_validate_prize_for_non_related_user(self):
        from ..models import Prize, PrizeUser
        from ..serializers import _validate_prize
        from whitelabel.test.util import APIUtilWhitelabel
        alice = User.objects.create(email='alice@test.com', username='alice')
        cosmic_whitelabel = APIUtilWhitelabel.create_whitelabel_market(alice, subdomain='cosmic')
        cosmic_prize = Prize(whitelabel_settings=cosmic_whitelabel, active=True)
        cosmic_prize.save()
        self.assertFalse(
            PrizeUser.objects.filter(user=alice, prize=cosmic_prize).exists())
        validated_prize = _validate_prize(cosmic_prize.subdomain, alice)
        self.assertEqual(validated_prize, cosmic_prize)
        self.assertTrue(
            PrizeUser.objects.filter(user=alice, prize=cosmic_prize).exists())

    def test_validate_prize_for_user_belonging_to_many_prizes(self):
        from ..models import Prize, PrizeUser
        from ..serializers import _validate_prize
        from whitelabel.test.util import APIUtilWhitelabel
        alice = User.objects.create(email='alice@test.com', username='alice')
        cosmic_whitelabel = APIUtilWhitelabel.create_whitelabel_market(alice, subdomain='cosmic')
        cosmic_prize = Prize(whitelabel_settings=cosmic_whitelabel, active=True)
        cosmic_prize.save()
        photonic_whitelabel = APIUtilWhitelabel.create_whitelabel_market(alice, subdomain='photonic')
        photonic_prize = Prize(whitelabel_settings=photonic_whitelabel, active=True)
        photonic_prize.save()
        PrizeUser.objects.create(user=alice, prize=cosmic_prize)
        PrizeUser.objects.create(user=alice, prize=photonic_prize)
        validated_prize = _validate_prize(cosmic_prize.subdomain, alice)
        self.assertEqual(validated_prize, cosmic_prize)
