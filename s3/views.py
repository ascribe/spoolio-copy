# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import json
import os

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.utils.datetime_safe import datetime as dt
from django.utils.http import urlquote_plus

from boto.s3.connection import Key
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from blobs.api import DigitalWorkEndpoint, OtherDataEndpoint, ThumbnailEndpoint
from blobs.models import File, DigitalWork, OtherData, Thumbnail
from s3.aws import sign_policy_document, sign_headers, is_valid_policy, get_bucket, get_client, get_host
from s3.models import save_request

__author__ = 'dimi'


def success_redirect_endpoint(request):
    """ This is where the upload will snd a POST request after the
    file has been stored in S3.
    """
    return make_response(200)


@api_view(['POST'])
def create_key(request):
    body = json.loads(request.body)

    filename = body['filename']
    _, extension = os.path.splitext(filename)
    uuid = body['uuid'] + extension if 'uuid' in body else filename

    # TODO handle key error - use serializer perhaps
    category = body['category']
    if category == 'digitalwork':
        category = '/'.join([body['uuid'], category])
    elif 'piece_id' in body:
        category = DigitalWork.piece_to_category(body['piece_id'], category)

    return Response({'key': File.create_key(category, uuid, request.user)},
                    content_type='application/json')


def handle_s3(request):
    """ View which handles all POST and DELETE requests sent by Fine Uploader
    S3. You will need to adjust these paths/conditions based on your setup.
    """
    if isinstance(request.user, AnonymousUser):
        return make_response(403, {'success': False})
    if request.method == "POST":
        return handle_post(request)
    elif request.method == "DELETE":
        return handle_delete(request)
    else:
        return HttpResponse(status=405)


def handle_post(request):
    """ Handle S3 uploader POST requests here. For files <=5MiB this is a simple
    request to sign the policy document. For files >5MiB this is a request
    to sign the headers to start a multipart encoded request.
    """
    if request.POST.get('success', None):
        return make_response(200)
    else:
        request_payload = json.loads(request.body)
        request_payload['expiration'] = (dt.utcnow() + datetime.timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ')

        headers = request_payload.get('headers', None)
        if headers:
            # The presence of the 'headers' property in the request payload
            # means this is a request to sign a REST/multipart request
            # and NOT a policy document
            response_data = sign_headers(headers)
            http_request = save_request(request.user, headers, multi_parts=3)
        else:
            if not is_valid_policy(request_payload, request.user):
                return make_response(400, {'invalid': True})
            response_data = sign_policy_document(request_payload)
            # TODO replace with S3HttpRequest model serializer
            http_request = save_request(request.user,
                                        {'request': request, 'payload': request_payload['conditions']},
                                        multi_parts=1)
        # TODO log it
        print http_request
        response_payload = json.dumps(response_data)

        return make_response(200, response_payload)


def handle_delete(request):
    """ Handle file deletion requests. For this, we use the Amazon Python SDK,
    boto.
    """
    key_name = request.GET['key']
    response = None

    # TODO: I see an opportunity to dance to funky beats here ... functools!!!!! @sylvain
    qs_other_data = OtherData.objects.filter(user=request.user, other_data_file=key_name).order_by('-pk')
    qs_digital_work = DigitalWork.objects.filter(user=request.user, digital_work_file=key_name).order_by('-pk')
    qs_thumbnail = Thumbnail.objects.filter(user=request.user, thumbnail_file=key_name).order_by('-pk')

    if qs_other_data:
        view = OtherDataEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=qs_other_data[0].pk)
    elif qs_digital_work:
        view = DigitalWorkEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=qs_digital_work[0].pk)
    elif qs_thumbnail:
        view = ThumbnailEndpoint.as_view({'delete': 'destroy'})
        response = view(request, pk=qs_thumbnail[0].pk)

    if response is None:
        return make_response(400, json.dumps({'success': False}))

    if response.status_code == status.HTTP_200_OK:
        aws_bucket = get_bucket()
        aws_key = Key(aws_bucket, key_name)
        aws_key.delete()
        # TODO replace with S3HttpRequest model serializer
        http_request = save_request(request.user,
                                    {'request': request,
                                     'payload':
                                         [{'key': key_name},
                                          {'bucket': aws_bucket.name}]
                                     },
                                    multi_parts=1)
        # TODO log it
        print http_request
    return response


def make_response(status=200, content=None):
    """ Construct an HTTP response. Fine Uploader expects 'application/json'.
    """
    response = HttpResponse()
    response.status_code = status
    response['Content-Type'] = "application/json"
    response.content = content
    return response


@api_view()
@permission_classes((AllowAny,))
def sign_url(request):
    body = request.query_params

    if 'title' in body and 'artist_name' in body and 'key' in body:
        # distrust all user input - we're escaping unsafe characters
        title = urlquote_plus(body['title'])
        artist_name = urlquote_plus(body['artist_name'])
        key = body['key']
        file_extension = os.path.splitext(key)[1]

        # prepare the responses content disposition header
        content_disposition_header = 'inline; filename={}-{}'.format(title, artist_name)
        # if the file to download actually has an extension, we're appending it
        # to the Content-Disposition header
        content_disposition_header += file_extension or '.file'

        # and request a presigned url from S3, so that the user is allowed
        # to download the renamed file
        conn = get_client()
        presigned_key = conn.generate_url(
            settings.AWS_PRESIGNED_URL_EXPIRY_TIME,
            'GET',
            settings.AWS_STORAGE_BUCKET_NAME,
            key,
            response_headers={
                'response-content-disposition': content_disposition_header
            },
        )

        presigned_key = presigned_key.replace('https://{}/'.format(settings.AWS_BUCKET_DOMAIN), '')
        signed_url = '{}/{}'.format(get_host(secure=True), presigned_key)

        return Response({'signed_url': signed_url}, status=status.HTTP_200_OK)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
