import json
from blobs.models import File

from s3 import aws

import os
import os.path

from piece.models import Piece
from util.models import JobMonitor
from zencoder import Zencoder
from django.conf import settings
from util.celery import app

AUDIO_FLASH_EXT = ['.ogg', '.wma']
AUDIO_HTML5_EXT = ['.mp3', '.wav']
AUDIO_SUPPORTED_EXT = AUDIO_FLASH_EXT + AUDIO_HTML5_EXT

VIDEO_FLASH_EXT = ['.mov', '.mpg', '.mpeg', '.m4v', '.ogv', '.avi']
VIDEO_HTML5_EXT = ['.webm', '.mp4']
VIDEO_SUPPORTED_EXT = VIDEO_FLASH_EXT + VIDEO_HTML5_EXT

def client():
    return Zencoder(settings.ZENCODER_API_KEY)


def encode(user, digital_work, output_extensions=None):
    response_id = zencode(user, digital_work, output_extensions=output_extensions)
    monitorEncoding(object_id=digital_work.id, resource_id=response_id, user=user)


def monitorEncoding(object_id, resource_id, user):
    job = JobMonitor(description=settings.JOB_CONVERTVIDEO,
                     object_id=object_id,
                     resource_id=resource_id,
                     percent_done=0,
                     user=user)
    job.save()
    updateMonitorEncoding.delay(job.id)
    return job


@app.task(bind=True, max_retries=None)
def updateMonitorEncoding(self, job):
    """
    Fetch the status of the Zencoder job and finalize

    :param job: JOB_CONVERTVIDEO - bitcoin_id carries the zencoder job_id
    """
    if type(job) is int:
        job = JobMonitor.objects.get(id=job, description=settings.JOB_CONVERTVIDEO)
    zencode_job_id = int(job.resource_id)

    job_str = 'Job ' + str(job.id)
    percent_done, state = zencodeProgress(zencode_job_id)
    job.percent_done = percent_done
    job.save()

    details = zencodeJobDetails(zencode_job_id)

    try:
        assert (state == 'finished')
        urls = [f['url'] for f in details['job']['output_media_files']]

        # Set thumbnail to frame if not chosen
        piece = Piece.objects.filter(digital_work_id=job.object_id)[0]
        thumbnail = piece.thumbnail
        if thumbnail.key == settings.THUMBNAIL_DEFAULT:

            thumb_keys = {
                k: piece.digital_work.associated_key('thumbnail', k + '/frame_0000.png')
                for k, v in settings.THUMBNAIL_SIZES.iteritems()}
            thumbnail.thumbnail_file = thumb_keys[settings.THUMBNAIL_SIZE_DEFAULT]

            thumb_urls = {
                k: File.url_safe_from_key(v)
                for k, v in thumb_keys.iteritems()}
            thumbnail.thumbnail_sizes = thumb_urls
            thumbnail.save()
            print thumbnail.key

        s = job_str + ': Video conversion completed and uploaded to:'
        for url in urls:
            s += str("\n\t-" + url)
        print s
    except AssertionError as e:
        # job is converted but needs to be uploaded...
        if job.percent_done == 100:
            job.percent_done = 99
        job.save()
        # see https://app.zencoder.com/docs/api/jobs/show
        print job_str + ': Video is converting on Zencoder - ' + str(int(job.percent_done)) + '%'
        self.retry(exc=e, countdown=15)


def zencode(user, fid, output_extensions=None):
    assert fid.extension() in VIDEO_SUPPORTED_EXT + AUDIO_SUPPORTED_EXT
    if output_extensions is None:
        if fid.extension() in VIDEO_SUPPORTED_EXT:
            output_extensions = VIDEO_HTML5_EXT
        elif fid.extension() in AUDIO_SUPPORTED_EXT:
            output_extensions = AUDIO_HTML5_EXT
        else:
            raise NotImplementedError

    s3_basename = os.path.splitext('/'.join([aws.get_s3_host(secure=True), fid.key]))[0]
    outputs = [{'label': e[1:],
                'url': s3_basename + e,
                'public': True,
                "notifications": {"url": "http://zencoderfetcher/"}}
               for e in output_extensions if not e == fid.extension()]
    [outputs.append(thumb) for thumb in thumbnail_output(s3_base_url(fid, 'thumbnail'))]

    response = client().job.create(fid.url, outputs=outputs)
    print "Zencoder Job created with id: " + str(response.body['id'])
    return response.body['id']


def s3_base_url(fid, category):
    return '/'.join([aws.get_s3_host(secure=True), fid.associated_key(category, '')])


def thumbnail_output(base_url):
    return [{"thumbnails": {"label": label,
                            "number": 1,
                            'public': True,
                            'size': label,
                            "base_url": base_url + label}}
            for label, size in settings.THUMBNAIL_SIZES.iteritems()]


def zencodeProgress(job_id):
    progress = json.loads(client().job.progress(job_id).raw_body)
    if progress['state'] == 'processing':
        percent_done = progress['progress']
    elif progress['state'] == 'finished':
        # todo : Job states include pending, waiting, processing, failed, and cancelled.
        percent_done = 100
    else:
        percent_done = 0
    return percent_done, progress['state']


def zencodeJobDetails(job_id):
    return json.loads(client().job.details(job_id).raw_body)
