# For python 3 compatibility
# see http://python-future.org/compatible_idioms.html#urllib-module
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import parse_qs, urlparse

from django.test import TestCase


class EmailsUtilsTests(TestCase):

    def test_get_signup_or_login_link_with_non_existing_user(self):
        from ..utils import get_signup_or_login_link
        email = 'idonotexist@nowhere.io'
        url = get_signup_or_login_link(email, 'www')
        parsed_url = urlparse(url)
        parsed_qs = parse_qs(parsed_url.query)
        self.assertNotIn('token', parsed_qs)
        self.assertIn('email', parsed_qs)
        self.assertIn('redirect', parsed_qs)
        self.assertIn('subdomain', parsed_qs)
        self.assertEqual(len(parsed_qs['email']), 1)
        self.assertEqual(len(parsed_qs['redirect']), 1)
        self.assertEqual(len(parsed_qs['subdomain']), 1)
        self.assertEqual(parsed_qs['email'][0], email)
        self.assertEqual(parsed_qs['redirect'][0], 'signup')
        self.assertEqual(parsed_qs['subdomain'][0], 'www')
