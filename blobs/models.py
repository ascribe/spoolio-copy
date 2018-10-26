import logging
import os
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.http import urlquote_plus

from cStringIO import StringIO

import urllib
from boto.s3.key import Key

from s3 import aws
from util.image import rotate_jpg_from_exif, resize_single_image_with_ratio, resize_gif_with_ratio
from util.celery import app
from util.models import JobMonitor
from util.util import hash_string
from PIL import Image

__author__ = 'dimi'

logger = logging.getLogger(__name__)

JPEG_FILE_EXTENSION = 'jpeg'
GIF_FILE_EXTENSION = 'gif'


class File(object):
    key = None
    user = None

    @staticmethod
    def create_key(category, filename, user=None, unique=True):
        if user:
            user_id = hash_string(str(user.id))
        else:
            user_id = 'anonymous'
        key = File._assemble_key(user_id, category, filename)
        # make unique 'filename-uuid'
        if unique:
            basename, ext = os.path.splitext(os.path.basename(filename))
            uid = uuid.uuid4()
            filename_inc = basename + '-' + str(uid) + ext
            key = File._assemble_key(user_id, category, filename_inc)
        return key

    @staticmethod
    def _assemble_key(user_id, category, filename):
        try:
            filename = filename.decode('utf-8')
        except UnicodeError as e:
            logger.warn(e)
        return "/".join([el for el in
                         [settings.DEPLOYMENT,
                          user_id,
                          category,
                          filename]
                         if el is not None]).lower()

    def type(self):
        return self.__class__.__name__

    def extension(self):
        return os.path.splitext(self.key)[1].lower()

    @property
    def basename(self):
        return os.path.basename(self.key)

    @property
    def filename_no_ext(self):
        return os.path.splitext(self.basename)[0]

    @property
    def url(self):
        return File.url_from_key(self.key)

    @property
    def url_safe(self):
        return File.url_safe_from_key(self.key)

    def upload(self, from_url):
        aws.upload(from_url, key=self.key)

    @staticmethod
    def url_safe_from_key(key):
        # NOTE Uses django.utils.http.quote_plus, see docs at
        # https://docs.djangoproject.com/en/1.8/ref/unicode/#uri-and-iri-handling
        return File.url_from_key(urlquote_plus(key))

    @staticmethod
    def url_from_key(key):
        return '%s/%s' % (aws.get_host(secure=True), key)

    @property
    def s3_file(self):
        return aws.get_files(self.key)[0]

    @property
    def size(self):
        return self.s3_file.size

    @property
    def mime(self):
        from encoder.zencoder_api import VIDEO_SUPPORTED_EXT, AUDIO_SUPPORTED_EXT

        if self.extension() in VIDEO_SUPPORTED_EXT:
            return 'video'
        elif self.extension() in AUDIO_SUPPORTED_EXT:
            return 'audio'
        elif self.extension() in ['.jpg', '.jpeg', '.gif', '.png', '.bmp', '.tiff', '.tif']:
            return 'image'
        elif self.extension() in ['.pdf']:
            return 'pdf'
        else:
            return 'other'

    @property
    def fineuploader_session(self):
        return {'name': os.path.split(self.key)[1],
                "uuid": self.id,
                's3Key': self.key,
                's3Bucket': "ascribe0",
                's3Url': self.url,
                's3UrlSafe': self.url_safe,
                'type': self.mime + '/' + self.extension()[1:]
                }

    def __unicode__(self):
        return unicode(self.url)


class Thumbnail(models.Model, File):
    user = models.ForeignKey(User, related_name='thumbnails_at_user', null=True)
    thumbnail_file = models.CharField(max_length=2000)
    thumbnail_sizes = HStoreField(null=True)

    @property
    def key(self):
        return self.thumbnail_file

    @key.setter
    def key(self, value):
        self.thumbnail_file = value

    @staticmethod
    @app.task
    def thumbnail_from_url(url, key, thumbnail, sizes=settings.THUMBNAIL_SIZES):

        # download the file
        filename, _ = urllib.urlretrieve(url)
        # TODO use os.path.splitext:
        # https://docs.python.org/2/library/os.path.html#os.path.splitext
        ext = filename.rpartition('.')[2]
        image = Image.open(filename)

        # jpegs are rotated according to their exif data
        if ext in ['jpeg', 'jpg']:
            image = rotate_jpg_from_exif(image)
            ext = JPEG_FILE_EXTENSION

        # create a thumbnail for size
        for label, size in sizes.iteritems():
            if ext == GIF_FILE_EXTENSION:
                # NOTE: resize_gif_with_ratio is calling save on img internally
                thumb_image = resize_gif_with_ratio(image, size, StringIO())
            else:
                thumb_image = StringIO()
                # NOTE: while we're calling it manually here
                _thumb_image = resize_single_image_with_ratio(image, size)
                # NOTE: For thumbnails, we want to convert all supported image
                #       formats (with the exception of gif) to jpeg, as it
                #       generally does the best job in compression for all types
                #       of images.
                ext = JPEG_FILE_EXTENSION
                _thumb_image.format = ext
                _thumb_image.save(thumb_image, ext)

            # upload to aws
            aws_key = Key(aws.get_bucket())
            aws_key.key = Thumbnail.build_aws_key(key, label, ext)
            aws_key.set_contents_from_string(thumb_image.getvalue())
            aws_key.make_public()

            # update thumbnail
            if label == settings.THUMBNAIL_SIZE_DEFAULT and thumbnail.thumbnail_file == settings.THUMBNAIL_DEFAULT:
                thumbnail.thumbnail_file = aws_key.key
            thumbnail.thumbnail_sizes[label] = File.url_safe_from_key(aws_key.key)
            thumbnail.save()

            logger.info('Thumbnail created and uploaded to: \n{}'.format(thumbnail.thumbnail_sizes[label]))

        return thumbnail

    @staticmethod
    def build_aws_key(key, label, extension):
        return '{}_thumbnails/{}/{}.{}'.format(
            key, label, str(uuid.uuid4()), extension)


class OtherData(models.Model, File):
    user = models.ForeignKey(User, related_name='other_datas_at_user', null=True)
    other_data_file = models.CharField(max_length=2000)

    @property
    def key(self):
        return self.other_data_file

    @key.setter
    def key(self, value):
        self.other_data_file = value


class DigitalWork(models.Model, File):
    user = models.ForeignKey(User, related_name='digital_works_at_user', null=True)
    digital_work_file = models.CharField(max_length=2000)
    digital_work_hash = models.CharField(max_length=2000)

    @property
    def key(self):
        return self.digital_work_file

    @key.setter
    def key(self, value):
        self.digital_work_file = value

    @property
    def hash(self):
        if self.digital_work_hash in [None, '']:
            try:
                self.digital_work_hash = aws.etag_hash(self.key)
                self.save()
            except AttributeError as e:
                print "couldnt find etag hash for %s (user: %s)" % (self.key, self.user.email)
                for key in aws.get_bucket().get_all_multipart_uploads():
                    if key.key_name == self.key:
                        try:
                            key.complete_upload()
                            blob = [i for i in aws.get_bucket().list(prefix=self.key)]
                            assert len(blob) > 0
                            self.digital_work_hash = aws.etag_hash(self.key)
                            self.save()
                        except Exception as e:
                            logging.warning(e.args)
                            return None

        return self.digital_work_hash

    def create_thumbnail(self):
        if self.mime == 'image':
            try:
                basename = self.associated_key('thumbnail', '', unique=False)
                thumbnail = Thumbnail(user=self.user,
                                      thumbnail_file=settings.THUMBNAIL_DEFAULT,
                                      thumbnail_sizes={k: self.url for k, v in settings.THUMBNAIL_SIZES.iteritems()})
                thumbnail.save()
                Thumbnail.thumbnail_from_url.delay(self.url, basename, thumbnail)
                return thumbnail
            except Exception as e:
                logger.error(e.message)
                return None
        return None

    @staticmethod
    def piece_to_category(piece_id, category):
        from piece.models import Piece
        try:
            piece = Piece.objects.get(id=piece_id)
            category = '/'.join([piece.digital_work.filename_no_ext, category])
        except ObjectDoesNotExist:
            pass
        return category

    @property
    def associated_piece(self):
        from piece.models import Piece

        return Piece.objects.get(digital_work_id=self.id)

    def associated_key(self, category, filename=None, user=None, unique=False):
        """
        create a key that corresponds starts with the same pieceid but a different category
        :return: DEPLOYMENT/USER/PIECEID/category/<filename>
        """
        if user is None:
            user = self.user
        if filename is None:
            filename = self.basename
        # FILENAME
        try:
            _, _, piece_id, digitalwork, _ = self.key.split('/')
        except ValueError:
            # old files with /media/...
            _, digitalwork, piece_id, _ = self.key.split('/')
        if digitalwork in ['digitalwork', 'digitalworkfile', 'digital_works']:
            category = '/'.join([piece_id, category])
        return File.create_key(category, filename, user, unique)

    @property
    def isEncoding(self):
        """
        check if video is encoding
        :return: False if not encoding or percentage done if encoding
        """
        if self.mime == 'video':
            # return 70
            try:
                job_encoding = JobMonitor.objects.filter(object_id=self.id,
                                                         description=settings.JOB_CONVERTVIDEO).order_by("-id")
                if job_encoding:
                    job_encoding = job_encoding[0]
                else:
                    return 0
                # JS in frontend says 0 == False
                if job_encoding.percent_done == 0:
                    return 1
                return job_encoding.percent_done
            except Exception:
                # should not occur, but to make sure this doesnt cause errors
                return 0
        return 0

    @property
    def encoding_urls(self):
        if self.mime == 'video':
            from encoder.zencoder_api import VIDEO_HTML5_EXT

            basename = os.path.splitext(self.url)[0]
            return [{'url': basename + e, 'label': e[1:]} for e in VIDEO_HTML5_EXT]
        return None
