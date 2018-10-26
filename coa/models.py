from django.contrib.auth.models import User
from django.db import models

import json
import unicodedata
from django.utils.http import urlquote_plus
import requests
from datetime import datetime

from boto.s3.key import Key

from blobs.models import File
from s3.aws import get_bucket
from util.celery import app
from util.crypto import import_env_key, sign
from django.conf import settings


class CoaFile(models.Model, File):
    user = models.ForeignKey(User, related_name='coa_files_at_user', null=True)
    coa_file = models.CharField(max_length=2000)
    # TODO would a foreign key to Edition make sense
    edition = models.IntegerField(blank=True, null=True)

    @property
    def key(self):
        return self.coa_file


@app.task
def create(username, edition):
    user = User.objects.get(username=username)
    coa_host = settings.ASCRIBE_PDF_URL
    from coa.serializers import CertificateEditionSerializer
    data = CertificateEditionSerializer(edition).data

    data['crypto_message'], _, data['crypto_signature'] = generate_crypto_message(edition)

    if data['thumbnail']['thumbnail_sizes'] is None:
        data['thumbnail'] = data['thumbnail']['url_safe']
    else:
        data['thumbnail'] = data['thumbnail']['thumbnail_sizes']['600x600']

    data['verify_owner_url'] = '{}coa_verify/'.format(settings.ASCRIBE_URL_FRONTEND)
    data['check_stamp_query'] = '?message={}&signature={}'.format(urlquote_plus(data['crypto_message']),
                                                                  urlquote_plus(data['crypto_signature']))
    data['check_stamp_url'] = '{}{}'.format(data['verify_owner_url'], data['check_stamp_query'])

    data['owner_timestamp'] = \
        edition._most_recent_transfer.datetime.strftime('%b. %d %Y, %X') \
        if edition._most_recent_transfer \
        else edition.datetime_registered.strftime('%b. %d %Y, %X')

    data['filename'] = edition.digital_work.extension()
    data['filesize'] = edition.digital_work.size
    response = requests.post(coa_host, data={'data': json.dumps(data)})
    assert response.status_code == 200, "Certificate could not be created due to an internal error, try again later"
    return upload(user, edition, response.content)


def generate_crypto_message(edition):
    priv_key = import_env_key('COA_PRIVKEY_1')
    message = "*".join([edition.artist_name,
                        edition.title,
                        str(edition.edition_number)+'/'+str(edition.num_editions),
                        str(edition.date_created.year),
                        edition.datetime_registered.strftime('%Y%b%d-%X')])
    message = unicodedata.normalize('NFKD', message).encode('ascii', 'ignore')
    (message_hash, signature) = sign(priv_key, message)
    return message, message_hash, signature


def upload(user, edition, content):
    k = Key(get_bucket())
    k.key = edition.digital_work.associated_key('coa', 'coa-%s.pdf' % datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))
    print 'CoA: start upload to S3'
    k.content_type = 'application/pdf'
    k.set_contents_from_string(content)
    k.make_public()
    print 'CoA: uploaded'
    coa_qs = CoaFile.objects.filter(user=user, edition=edition.id)
    if coa_qs:
        coa_qs.update(coa_file=k.key)
        coa = coa_qs[0]
    else:
        coa = CoaFile.objects.create(user=user, edition=edition.id, coa_file=k.key)
    edition.coa = coa
    edition.save()
    return coa
