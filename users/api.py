import logging

from django.conf import settings
from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import LANGUAGE_SESSION_KEY, check_for_language
# TODO add & test
# from django.views.decorators.cache import never_cache
# from django.views.decorators.debug import sensitive_post_parameters

from rest_framework.decorators import list_route
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from oauth2_provider.ext.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.models import AccessToken

from users.models import (
    User,
    UserProfile,
    UserNeedsToRegisterRole,
    UserValidateEmailRole,
    UserRequestResetPasswordRole,
    UserResetPasswordRole
)
from users.permissions import IsAuthenticatedOrSignUpOnly
from users.serializers import (
    LoginForm,
    ActivateForm,
    RequestResetPasswordForm,
    ResetPasswordForm,
    UsernameSerializer,
    WebUserSerializer,
    ApiUserSerializer,
    UserProfileForm,
    userNeedsRegistration,
    createUsername
)
from users.signals import check_pending_actions

from bitcoin.models import BitcoinWallet

from util import util
from util.decorators.csrf import strict_referer_checking
from util.util import insert_or_change_subdomain, extract_subdomain

from emails import messages
from emails.tasks import send_ascribe_email
from web.api_util import GenericViewSetKpi

logger = logging.getLogger(__name__)


# The GenericViewSet allows us to set the serializer class
# with get_serializer_class. By default it passes the request context to
# the serializer. We can also override this behaviour by overriding
# get_serializer_context
class UserEndpoint(GenericViewSetKpi):
    """
    User API endpoint
    """
    # default queryset. We can override this on the view methods
    queryset = User.objects.all()
    # When writing class based views there is no easy way to override the
    # permissions for invidual view methods. The easiest way is to
    # create custom permission classes
    permission_classes = [IsAuthenticatedOrSignUpOnly]
    json_name = 'users'

    # Not sure if we want to have an endpoint to list all users!!!
    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, self.json_name: serializer.data},
                        status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()

        try:
            user = queryset.get(pk=pk)
        except ObjectDoesNotExist:
            user = None

        if user:
            serializer = self.get_serializer(user)
            return Response({'success': True, self.json_name[:-1]: serializer.data},
                            status=status.HTTP_200_OK)
        else:
            return Response({'success': False},
                            status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            application = None
            if hasattr(request.auth, 'token'):
                application = AccessToken.objects.get(token=request.auth.token).application

            lang = translation.get_language() or settings.LANGUAGE_CODE
            # TODO clarify whether we'll need the LANGUAGE_SESSION_KEY at all
            # if hasattr(request, "session") and request.session.has_key(translation.LANGUAGE_SESSION_KEY):
            #    lang = request.session[translation.LANGUAGE_SESSION_KEY]

            subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key('HTTP_ORIGIN') else 'www'
            token = data['token'] if 'token' in data.keys() else None

            user = UserEndpoint._createNewUser(data['email'],
                                               data['password'],
                                               application=application,
                                               lang=lang,
                                               subdomain=subdomain,
                                               token=token)
            if not token:
                serializer = self.get_serializer(user)
                return Response({'success': True, self.json_name[:-1]: serializer.data}, status=status.HTTP_201_CREATED)
            else:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth.login(request, user)
                redirect_url = insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND + '?first_time=1', subdomain)
                return Response({'success': True, 'redirect': redirect_url}, status=status.HTTP_201_CREATED)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['get'], permission_classes=[AllowAny])
    def activate(self, request):
        if request.user.is_authenticated():
            auth.logout(request)
        form = ActivateForm(data=request.query_params)
        if form.is_valid():
            user = form.validated_data['email']
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth.login(request, user)
            activate_role = UserValidateEmailRole.objects.filter(user=user).order_by("-datetime")[0]
            activate_role.confirm()
            activate_role.save()
            logger.info('user activated')
            # create redirect with subdomain inserted
            redirect_url = insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND + '?first_time=1',
                                                      form.validated_data['subdomain'])
            return HttpResponseRedirect(redirect_url)
        else:
            qp = request.query_params.copy()
            qp.pop('token', None)
            redirect_url = insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND + 'login?' + qp.urlencode(),
                                                      request.query_params.get('subdomain', 'www'))
            return HttpResponseRedirect(redirect_url)

    @list_route(methods=['get', 'post'], permission_classes=[AllowAny])
    # @method_decorator(sensitive_post_parameters)   # TODO add & test
    @method_decorator(strict_referer_checking)
    # @method_decorator(never_cache)    # TODO add & test
    def login(self, request):
        if request.user.is_authenticated():
            auth.logout(request)

        form = LoginForm(data=request.data)
        if form.is_valid():
            email = form.validated_data['email']
            password = form.validated_data['password']
            username = User.objects.get(email=email).username
            # TODO Review. Authentication is done twice. Here & in serializer LoginForm
            user = auth.authenticate(username=username, password=password)
            auth.login(request, user)
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['get'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        if request.user is not None:
            auth.logout(request)
        return Response({'success': True}, status=status.HTTP_200_OK)

    @list_route(methods=['post'], permission_classes=[AllowAny])
    def request_reset_password(self, request):
        serializer = RequestResetPasswordForm(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['email']
            if user:
                role = UserRequestResetPasswordRole.create(user)
                role.save()
                subdomain = extract_subdomain(request.META['HTTP_ORIGIN']) if request.META.has_key(
                    'HTTP_ORIGIN') else 'www'
                redirect_url = insert_or_change_subdomain(settings.ASCRIBE_URL_FRONTEND + 'password_reset', subdomain)
                lang = translation.get_language() or settings.LANGUAGE_CODE
                send_ascribe_email.delay(
                    msg_cls='PasswordResetEmailMessage',
                    to=user.email,
                    token=role.token,
                    redirect_url=redirect_url,
                    lang=lang,
                )
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        if request.user.is_authenticated():
            auth.logout(request)
        serializer = ResetPasswordForm(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['email']
            password = serializer.validated_data['password']
            # update user
            UserResetPasswordRole.create(user=user).save()
            user.set_password(password)
            user.save()
            request_role = UserRequestResetPasswordRole.objects.filter(user=user).order_by("-datetime")[0]
            request_role.confirm()
            request_role.save()
            # update bitcoin wallet
            wallet = BitcoinWallet.objects.get(user=user)
            pubkey = BitcoinWallet.pubkeyFromPassword(user, password)
            wallet.public_key = pubkey
            wallet.save()
            # login
            user = auth.authenticate(username=user.username, password=password)
            auth.login(request, user)

            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def username(self, request):
        serializer = UsernameSerializer(data=request.data)
        if serializer.is_valid():
            request.user.username = serializer.validated_data['username']
            request.user.save()
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['get'], permission_classes=[IsAuthenticated])
    def wallet_settings(self, request):
        wallet = BitcoinWallet.walletForUser(request.user)
        btc_public_key = wallet.public_key
        btc_root_address = wallet.rootAddress

        json_data = {'btc_public_key': btc_public_key,
                     'btc_root_address': btc_root_address}
        return Response({'success': True, 'wallet_settings': json_data}, status=status.HTTP_200_OK)

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def set_language(self, request):
        """
        Redirect to a given url while setting the chosen language in the
        session or cookie. The url and the language code need to be
        specified in the request parameters.

        Since this view changes how the user will see the rest of the site, it must
        only be accessed as a POST request. If called as a GET request, it will
        redirect to the page in the request (the 'next' parameter) without changing
        any state.
        """
        from django.conf import settings as lazy_settings

        response = Response({'success': True}, status=status.HTTP_200_OK)

        lang_code = request.data['language']
        if lang_code and check_for_language(lang_code):
            if hasattr(request, 'session'):
                request.session[LANGUAGE_SESSION_KEY] = lang_code
            else:
                response.set_cookie(lazy_settings.LANGUAGE_COOKIE_NAME, lang_code,
                                    max_age=lazy_settings.LANGUAGE_COOKIE_AGE,
                                    path=lazy_settings.LANGUAGE_COOKIE_PATH,
                                    domain=lazy_settings.LANGUAGE_COOKIE_DOMAIN)
        return response

    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            profile = data.pop('email')
            UserProfile.objects.filter(id=profile.id).update(**data)
            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        # Use the API serializer if the user is using the oauth token
        # else default to the Web serializer
        if isinstance(self.request.successful_authenticator,
                      OAuth2Authentication):
            return ApiUserSerializer
        if self.action == 'profile':
            return UserProfileForm
        return WebUserSerializer

    def get_queryset(self):
        # return an empty queryset by default
        users = User.objects.none()
        # API: only show the users that have the same client application
        if hasattr(self.request.auth, 'token'):
            app = AccessToken.objects.get(token=self.request.auth.token).application
            # filter by foreign key. Kinda cool
            users = User.objects.filter(Q(userprofile__created_by=app) | Q(email=self.request.user.email))
        else:
            users = User.objects.filter(email=self.request.user.email)

        return users

    # TODO extract a method out for the invited case,.e.g.:
    # def create_and_invite_user(email, **kwargs):
    #    if not username:
    #        username = createUsername(email.split('@')[0][:30])
    #    user = User.objects.create_user(username, email, password)
    #    UserNeedsToRegisterRole.create(user=user, role=None).save()
    #    return user
    @staticmethod
    def _createNewUser(email,
                       password,
                       username=None,
                       application=None,
                       invited=False,
                       lang=settings.LANGUAGE_CODE,
                       subdomain="www",
                       token=None):

        pending_actions = False

        if not username:
            username = createUsername(email.split('@')[0][:30])
        user = userNeedsRegistration(email)

        # user exists in DB. Was it created by an invite?
        if user is not None:
            user.set_password(password)
            user.save()
            # BitcoinWallet.objects.get(user=user).delete()
            UserNeedsToRegisterRole.objects.get(user=user, type="UserNeedsToRegisterRole").delete()
            pending_actions = True

        else:
            user = User.objects.create_user(username, email, password)
            if invited:
                UserNeedsToRegisterRole.create(user=user, role=None).save()
                return user
        try:
            user_profile = UserProfile.objects.get(user=user)
        except ObjectDoesNotExist:
            user_profile = UserProfile.objects.create(user=user, created_by=application)
            user_profile.save()

        # create bitcoin account
        # there should only be one wallet. but just in case
        old_wallet = BitcoinWallet.objects.filter(user=user)
        if len(old_wallet) > 0:
            for w in old_wallet:
                w.delete()
        BitcoinWallet.create(user, password=password).save()

        # after the wallet is created we can check the pending actions
        if pending_actions:
            check_pending_actions.send(sender=UserEndpoint, user=user)

        if not token:
            validate_email_role = UserValidateEmailRole.create(user)
            validate_email_role.save()
            # TODO put this logic somewhere else
            if subdomain == 'cc':
                msg_cls = messages.WelcomeEmailMessageCreativeCommons
            elif subdomain == '23vivi':
                msg_cls = messages.WelcomeEmailMessage23vivi
            elif subdomain == 'lumenus':
                msg_cls = messages.WelcomeEmailMessageLumenus
            elif subdomain == 'polline':
                msg_cls = messages.WelcomeEmailMessagePolline
            elif subdomain == 'artcity':
                msg_cls = messages.WelcomeEmailMessageArtcity
            elif subdomain == 'demo':
                msg_cls = messages.WelcomeEmailMessageDemo
            elif subdomain == 'liquidgallery':
                msg_cls = messages.WelcomeEmailMessageLiquidGallery
            else:
                msg_cls = messages.WelcomeEmailMessage
            send_ascribe_email.delay(
                msg_cls=msg_cls,
                to=user.email,
                token=validate_email_role.token,
                subdomain=subdomain,
                lang=lang,
            )
        else:
            validate_email_role = UserValidateEmailRole.objects.filter(user=user).order_by("-datetime")[0]
            assert validate_email_role.token == token
            validate_email_role.confirm()
            validate_email_role.save()
        return user


def createOrGetUser(email, subdomain="www"):
    email = email.lower()
    if len(User.objects.filter(Q(email=email) | Q(username=email))):
        # case: email exists
        return User.objects.get(email=email)
    else:
        # case: email doesnt exists
        try:
            return UserEndpoint._createNewUser(email, util.randomStr(10), invited=True, subdomain=subdomain)
        except Exception, e:
            msg = 'Unable to create new account for %s. Error: %s' % (email, e)
            raise Exception(msg)
