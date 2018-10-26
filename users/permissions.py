from rest_framework import permissions


class IsAuthenticatedOrSignUpOnly(permissions.BasePermission):
    """
    Custom permission that always requires authentication
    except to create users
    """
    def has_permission(self, request, view):
        # If user is authenticated he can access all views
        if request.user.is_authenticated():
            return True
        # If user is not authenticated he can only create a user.
        # This is for the sign up form
        elif view.action == 'create':
            return True
        return False
