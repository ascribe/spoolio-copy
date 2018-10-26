import base64
import hmac
import json
import os.path
import time
import urllib2
from hashlib import sha1
from StringIO import StringIO

from django.conf import settings

import boto
from boto.s3.key import Key
import pybitcointools

import util.util as util


def get_client():
    return boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)


def get_bucket():
    return get_client().get_bucket(settings.AWS_STORAGE_BUCKET_NAME)


def get_host(secure=False):
    http = 'http'
    if secure:
        http = 'https'
    return '%s://%s' % (http, settings.AWS_CLOUDFRONT_DOMAIN)


def get_s3_host(secure=False):
    http = 'http'
    if secure:
        http = 'https'
    return '%s://%s.s3.amazonaws.com' % (http, settings.AWS_STORAGE_BUCKET_NAME)


def chmod_public_dir(dirname='', bucket=None):
    if not bucket:
        bucket = get_bucket()
    all_users = 'http://acs.amazonaws.com/groups/global/AllUsers'
    for key in bucket.list(prefix=dirname):
        readable = False
        acl = key.get_acl()
        for grant in acl.acl.grants:
            if grant.permission == 'READ':
                if grant.uri == all_users:
                    readable = True
        if not readable:
            key.make_public()


def get_files(dirname='', bucket=None):
    if not bucket:
        bucket = get_bucket()
    return [item for item in bucket.list(prefix=dirname)]


def ls(dirname='', bucket=None):
    if not bucket:
        bucket = get_bucket()
    bucket_name = bucket.name
    url = []
    for file in get_files(dirname, bucket):
        url.append(file.name)
        print "/".join([bucket_name, url[-1]])
    return url


def rmdir(dirname='', bucket=None, force=False):
    if not bucket:
        bucket = get_bucket()
    if dirname == '' and not force:
        raise Exception('avoided deleting everything... Huray! (set force=True)')
    for key in bucket.list(prefix=dirname):
        key.delete()


def rmkey(key='', bucket=None):
    if not bucket:
        bucket = get_bucket()
    bucket.delete_key(key)


def upload(from_url, key, bucket=None):
    if not bucket:
        bucket = get_bucket()
    k = Key(bucket)
    k.key = key
    file_object = urllib2.urlopen(from_url)
    fp = StringIO(file_object.read())   # Wrap object
    k.set_contents_from_file(fp)
    k.make_public()


def uniqueSavePathName(dirname, filename):
    basename, ext = os.path.splitext(filename)
    try:
        basename_hash = pybitcointools.sha256(basename)
    except Exception:
        basename_hash = util.randomStr(64)
    return os.path.join(dirname, str(time.time()).replace('.', ''), basename_hash + ext)


def is_valid_path(path, user):
    key_base = '/'.join([settings.DEPLOYMENT, util.hash_string(str(user.id))])
    return path.startswith(key_base.lower())


# TODO review & verify whether policy_document could be structured differently,
# such as a key-value pair structure instead of a list. This would ease the
# verification
def is_valid_policy(policy_document, user):
    """ Verify the policy document has not been tampered with client-side
    before sending it off.
    """
    # bucket = settings.AWS_EXPECTED_BUCKET
    # parsed_max_size = settings.AWS_MAX_SIZE
    bucket = ''
    parsed_max_size = 0

    for condition in policy_document['conditions']:
        if isinstance(condition, list) and condition[0] == 'content-length-range':
            parsed_max_size = int(condition[2])
        else:
            if condition.get('bucket', None):
                bucket = condition['bucket']

    key_entries = filter(lambda x: 'key' in x, policy_document['conditions'])

    return (bucket == settings.AWS_STORAGE_BUCKET_NAME and
            parsed_max_size in settings.AWS_MAX_SIZE and
            all(map(lambda x: is_valid_path(x['key'], user), key_entries)))


def sign_policy_document(policy_document):
    """ Sign and return the policy doucument for a simple upload.
    http://aws.amazon.com/articles/1434/#signyours3postform
    """
    policy = base64.b64encode(json.dumps(policy_document))
    signature = base64.b64encode(hmac.new(settings.AWS_SECRET_ACCESS_KEY, policy, sha1).digest())
    return {
        'policy': policy,
        'signature': signature
    }


def sign_headers(headers):
    """ Sign and return the headers for a chunked upload. """
    return {
        'signature': base64.b64encode(hmac.new(settings.AWS_SECRET_ACCESS_KEY, headers, sha1).digest())
    }


def etag_hash(key):
    return get_bucket().get_key(key).etag.strip("\"")
