from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions
from prize.models import Prize
from prize.models import PrizeUser


class IsAuthenticatedAndAdmin(permissions.BasePermission):
    """
    Custom permission that always requires authentication
    except to create users
    """
    def has_permission(self, request, view):
        # If user is authenticated he can access all views
        if not request.user.is_authenticated():
            return False
        return has_prize_permission(request.user, request.parser_context['kwargs']['domain_pk'], is_admin=True)


class IsAuthenticatedAndJury(permissions.BasePermission):
    """
    Custom permission that always requires authentication
    except to create users
    """
    def has_permission(self, request, view):
        # If user is authenticated he can access all views
        if not request.user.is_authenticated():
            return False
        return has_prize_permission(request.user,
                                    request.parser_context['kwargs']['domain_pk'], is_jury=True)


def has_prize_permission(user, prize_name, **kwargs):
    prize = Prize.objects.get(whitelabel_settings__subdomain=prize_name)
    # TODO test and replace with:
    # return PrizeUser.objects.filter(
    #     user=user,
    #     prize=prize,
    #     datetime_deleted=None,
    #     **kwargs
    # ).exists()
    try:
        PrizeUser.objects.get(user=user, prize=prize, datetime_deleted=None, **kwargs)
        return True
    except ObjectDoesNotExist:
        return False
