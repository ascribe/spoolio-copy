import re
import datetime
from django.contrib.auth.models import User
from django.contrib.postgres.fields import HStoreField

from django.db import models, connection
from django.utils.timezone import utc
from django.db import transaction

__author__ = 'dimi'


def string_list_to_dict(list, delimiter='='):
    result = dict()
    for _item in list:
        _item = re.split(delimiter, _item)
        if len(_item) == 1:
            result[_item[0]] = None
        elif len(_item) > 1:
            result[_item[0]] = ':'.join(_item[1:])
    return result


class S3HttpRequest(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, related_name='httprequest_created')
    datetime_created = models.DateTimeField(auto_now_add=True)
    headers = HStoreField(null=True)
    verb = models.CharField(max_length=10)
    path = models.TextField()
    query_params = HStoreField(null=True)
    upload_speed_kbs = models.IntegerField(null=True, blank=True)

    @classmethod
    def create(cls, user, verb, path, headers=None, query_params=None, multi_parts=1):
        obj = cls(user=user,
                  verb=verb,
                  headers=headers,
                  path=path,
                  query_params=query_params)
        obj.upload_speed_kbs = obj.compute_upload_speed_kbs(multi_parts)
        return obj

    @staticmethod
    def parse(request):
        if isinstance(request, basestring):
            _req = filter(None, re.split('\n|\r', request))
            verb, headers, = [_req[0], string_list_to_dict(_req[1:-1], ':')]
            _path = re.split('\?', _req[-1])
            path = _path[0]
            query_params = string_list_to_dict(re.split('&', _path[1]))
            return verb, headers, path, query_params
        elif isinstance(request, dict):
            verb = request['request'].method
            _headers = [item for item in request['payload'] if isinstance(item, dict)]

            headers = { k: v for d in _headers for k, v in d.items() }
            path = "/" + "/".join([headers['bucket'], headers['key']])
            return verb, headers, path, None
        return None

    def compute_upload_speed_kbs(self, multi_parts=1, part_size_kb=5 * 1024):
        try:
            assert self.verb in ['PUT', 'POST']
            assert self.datetime_created
            if self.verb == 'PUT':
                assert 'partNumber' in self.query_params.keys()
                part_num = int(self.query_params['partNumber'])
                num_parts = part_num - multi_parts
                post = S3HttpRequest.objects.get(user=self.user, verb='POST', path=self.path)
            else:
                post = S3HttpRequest.objects.filter(user=self.user, verb='POST', path=self.path)\
                    .order_by("datetime_created")
                assert len(post) > 1
                post = post[0]
                put = S3HttpRequest.objects.filter(user=self.user, verb='PUT', path=self.path)\
                    .order_by("-datetime_created")
                assert len(put) > 0
                put = put[0]
                assert 'partNumber' in put.query_params.keys()
                num_parts = int(put.query_params['partNumber'])
            time = self.datetime_created - post.datetime_created
            speed = num_parts * part_size_kb / time.total_seconds()
            return int(speed) if speed > 0 else None
        except:
            return None

    def __unicode__(self):
        speed = str(self.upload_speed_kbs) if self.upload_speed_kbs else '-'
        return u'<S3HttpRequest> %s key:%s user:%s kbs:%s' % (self.verb, self.path, self.user.email, speed)


@transaction.atomic
def save_request(user, request, multi_parts=1):
    verb, headers, path, query_params = S3HttpRequest.parse(request)
    if verb == 'PUT':
        S3HttpRequest.objects.filter(user=user,
                                     verb=verb,
                                     path=path).delete()
    http_request = S3HttpRequest.create(user=user, verb=verb, path=path)
    http_request.save()
    http_request.headers = headers
    http_request.query_params = query_params
    http_request.datetime_created = datetime.datetime.utcnow().replace(tzinfo=utc)
    http_request.upload_speed_kbs = http_request.compute_upload_speed_kbs(multi_parts=multi_parts)
    http_request.save()
    return http_request
