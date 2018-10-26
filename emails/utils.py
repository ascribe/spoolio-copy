import urllib

from django.conf import settings
from django.contrib.auth.models import User

from users.models import UserNeedsToRegisterRole, UserValidateEmailRole
from util.util import insert_or_change_subdomain


def get_signup_or_login_link(email_to, subdomain):
    email_safe = urllib.quote_plus(email_to.encode('ascii'))
    redirect_url = insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND, subdomain)
    try:
        user = User.objects.get(email=email_to)
    except User.DoesNotExist:
        # user has not been created, send to signup without token
        return '{}?email={}&subdomain={}&redirect=signup'.format(redirect_url, email_safe, subdomain)
    try:
        UserNeedsToRegisterRole.objects.get(user=user,
                                            type="UserNeedsToRegisterRole")
    except UserNeedsToRegisterRole.DoesNotExist:
        # user has signed up, send to login
        return '{}?email={}&subdomain={}&redirect=login'.format(redirect_url, email_safe, subdomain)

    else:
        # user was invited, send to signup with token for implicit email validation
        # validation only requires the last created token
        validate_role = UserValidateEmailRole.create(user=user)
        validate_role.save()
        return '{}?token={}&email={}&subdomain={}&redirect=signup'.format(redirect_url, validate_role.token, email_safe,
                                                                          subdomain)
