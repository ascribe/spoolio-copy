from django.http import HttpResponse
from django.http.request import urlsplit
from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest

from rest_framework import viewsets, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from oauth2_provider.ext.rest_framework.authentication import OAuth2Authentication

import json
import logging
from core.pagination import NamedPageNumberPagination


def json_api(function):
    def function_wrapper(*args, **kwargs):
        try:
            request_id = [i for i, arg in enumerate(args) if isinstance(arg, WSGIRequest)]
            if len(request_id):
                request_id = request_id[0]
                if hasattr(args[request_id], 'resource_owner') and \
                        isinstance(args[request_id].user, AnonymousUser):
                    args[request_id].user = args[request_id].resource_owner

            json_result = function(*args, **kwargs)
            return SuccessJsonResponse(json_result)
        except Exception as e:
            return ErrorJsonResponse(e.message)

    return function_wrapper


def ErrorJsonResponse(err_message):
    print err_message
    return HttpResponse(json.dumps({'success': False, 'error': err_message}), content_type='application/json',
                        status=500)


def SuccessJsonResponse(serialized_dict=None):
    json_obj = {'success': True}
    if serialized_dict:
        json_obj = dict(json_obj, **serialized_dict)
    return HttpResponse(JSONRenderer().render(json_obj), content_type='application/json')


class PaginatedGenericViewset(viewsets.GenericViewSet):
    json_name = 'results'
    pagination_class = NamedPageNumberPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.paginator.get_paginated_response(serializer.data,
                                                         name=self.json_name,
                                                         unfiltered_count=kwargs.get('unfiltered_count',
                                                                                     len(self.get_queryset())))

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response({'success': True, self.json_name: serializer.data}, status=status.HTTP_200_OK)


LOGGER = logging.getLogger('KPI')


class DRFLoggerMixin(object):
    """
    Log all requests to DRF

    As seen on https://gist.github.com/Karmak23/2ea1d62ea32edbeed07b
    """

    def initial(self, request, *args, **kwargs):
        try:
            data = request.DATA
        except:
            LOGGER.exception('Exception while getting request.DATA')
        else:
            try:
                data = json.dumps(data, sort_keys=True, indent=2)
            except:
                pass

            # check if user is anonymous
            user = 'anonymous'
            if not request.user.is_anonymous():
                user = request.user.email

            # Check authenticator
            authenticator = 'unknown'
            if isinstance(request.successful_authenticator, OAuth2Authentication):
                authenticator = 'api'
            elif isinstance(request.successful_authenticator, SessionAuthentication):
                authenticator = 'webapp'

            # check path and query params
            url = urlsplit(request.get_full_path())
            path = url.path
            # query = json.dumps(QueryDict(url.query).dict())

            LOGGER.info(u'%(method)s %(path)s %(user)s'
                        u' %(origin)s'
                        u' %(auth)s' % {
                            'method': request.method,
                            'user': user,
                            'path': path,
                            'origin': request.META.get('HTTP_HOST', u'Unknown'),
                            'auth': authenticator
                        }
                        )

        return super(DRFLoggerMixin, self).initial(request, *args, **kwargs)


class GenericViewSetKpi(DRFLoggerMixin, viewsets.GenericViewSet):
    pass


class PaginatedGenericViewSetKpi(DRFLoggerMixin, PaginatedGenericViewset):
    pass




