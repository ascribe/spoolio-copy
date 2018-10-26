import logging

from django.middleware.csrf import (CsrfViewMiddleware,
                                    REASON_NO_REFERER, REASON_BAD_REFERER)
from django.utils.decorators import decorator_from_middleware
from django.utils.encoding import force_text
from django.utils.http import same_origin


class _StrictRefererChecking(CsrfViewMiddleware):

    def process_view(self, request, callback, callback_args, callback_kwargs):
        """
        Taken from django.middleware.csrf
        """
        if request.is_secure():
            # Suppose user visits http://example.com/
            # An active network attacker (man-in-the-middle, MITM) sends a
            # POST form that targets https://example.com/detonate-bomb/ and
            # submits it via JavaScript.
            #
            # The attacker will need to provide a CSRF cookie and token, but
            # that's no problem for a MITM and the session-independent
            # nonce we're using. So the MITM can circumvent the CSRF
            # protection. This is true for any HTTP connection, but anyone
            # using HTTPS expects better! For this reason, for
            # https://example.com/ we need additional protection that treats
            # http://example.com/ as completely untrusted. Under HTTPS,
            # Barth et al. found that the Referer header is missing for
            # same-domain requests in only about 0.2% of cases or less, so
            # we can use strict Referer checking.
            referer = force_text(
                request.META.get('HTTP_REFERER'),
                strings_only=True,
                errors='replace'
            )
            if referer is None:
                return self._reject(request, REASON_NO_REFERER)

            # Note that request.get_host() includes the port.
            good_referer = 'https://%s/' % request.get_host()
            if not same_origin(referer, good_referer):
                reason = REASON_BAD_REFERER % (referer, good_referer)
                return self._reject(request, reason)

        return self._accept(request)

    def process_response(self, request, response):
        return response


strict_referer_checking = decorator_from_middleware(_StrictRefererChecking)
strict_referer_checking.__name__ = 'strict_referer_checking'
strict_referer_checking.__doc__ = """
Use this decorator on views that need a strict referer verification, but
without the other CSRF protection mechanisms that csrf_protect enforces.
"""
