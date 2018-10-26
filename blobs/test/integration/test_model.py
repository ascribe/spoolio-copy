# -*- encoding: utf-8 -*-

import hashlib

from mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.datetime_safe import datetime
from urlparse import urlparse

from blobs.models import File, DigitalWork, Thumbnail, OtherData
from django.conf import settings

import urllib
from PIL import Image


__author__ = 'dimi'

FIX_URL_JPG='http://ascribe0.s3.amazonaws.com/media/thumbnails/ascribe_spiral.png'
FIX_KEY_PNG='ascribe_spiral.png'


def create_user_admin():
    password_admin = settings.DJANGO_PYCOIN_ADMIN_PASS
    user_admin = User.objects.create(username="mysite_user", email="admin@keidom.com", password=password_admin)
    return user_admin, password_admin


def create_user_test():
    password_test = 'test'
    user_test = User.objects.create(username="testuser", email="testuser@keidom.com", password=password_test)
    return user_test, password_test


def hash_string(str):
    md5 = hashlib.md5()
    md5.update(str)
    return md5.hexdigest()


class FileTestCase(TestCase):
    def setUp(self):
        """
        generate user data
        """
        self.user_admin, self.password_admin = create_user_admin()
        self.user_test, self.password_test = create_user_test()
        self.date = datetime.strptime('24052010', "%d%m%Y").date()

    def compare_file(self, save_file, find_file):
        self.assertEqual(save_file.id, find_file.id)
        self.assertEqual(save_file.url, find_file.url)
        self.assertEqual(save_file.key, find_file.key)
        self.assertEqual(save_file.user.username, find_file.user.username)

    @patch('uuid.uuid4')
    def test_create_key(self, mock_uuid):
        uid = 'e91dfc72-a19f-4da8-bdb1-70230cf35ab6'
        mock_uuid.return_value = uid
        user_hash = hash_string(str(self.user_test.id))
        # digitalwork - anonymous
        digitalwork_key = File.create_key("digitalwork", "test.png", None)
        self.assertEqual(digitalwork_key, 'local/anonymous/digitalwork/test-{}.png'.format(uid))
        # digitalwork
        digitalwork_key = File.create_key("digitalwork", "test.png", self.user_test)
        self.assertEqual(digitalwork_key, 'local/' + user_hash + '/digitalwork/test-{}.png'.format(uid))
        # digitalwork key exists
        digitalwork_key = File.create_key("digitalwork", FIX_KEY_PNG, self.user_test)
        self.assertEqual(digitalwork_key, 'local/' + user_hash + '/digitalwork/ascribe_spiral-{}.png'.format(uid))
        # thumbnail - anonymous
        thumbnail_key = File.create_key("thumbnail", "test.png", None)
        self.assertEqual(thumbnail_key, 'local/anonymous/thumbnail/test-{}.png'.format(uid))
        # thumbnail
        thumbnail_key = File.create_key("thumbnail", FIX_KEY_PNG, self.user_test)
        self.assertEqual(thumbnail_key, 'local/' + user_hash + '/thumbnail/ascribe_spiral-{}.png'.format(uid))

    def test_create_non_unique_key(self):
        digitalwork_key = File.create_key('digitalwork', 'test.png', unique=False)
        self.assertEqual(digitalwork_key, 'local/anonymous/digitalwork/test.png')

    @patch('uuid.uuid4')
    def test_create_unique_key_with_uuid(self, mock_uuid):
        uid = 'e91dfc72-a19f-4da8-bdb1-70230cf35ab6'
        mock_uuid.return_value = uid

        digitalwork_key = File.create_key('digital_work', 'test.png')
        self.assertEqual(digitalwork_key,
                         'local/anonymous/digital_work/test-e91dfc72-a19f-4da8-bdb1-70230cf35ab6.png')
        self.assertEqual(mock_uuid.call_count, 1)

    def test_create_digital_work(self):
        save_file = DigitalWork(user=self.user_test,
                                digital_work_file='local/testuser/ascribe_spiral/digitalwork/ascribe_spiral.png')
        save_file.save()
        self.assertEqual(save_file.hash, 'f702fe80edf519e8fd3a4242fbafef63')
        self.assertEqual(save_file.extension(), '.png')
        self.assertEqual(save_file.basename, 'ascribe_spiral.png')
        self.assertEqual(save_file.key, 'local/testuser/ascribe_spiral/digitalwork/ascribe_spiral.png')
        self.assertEqual(urlparse(save_file.url).path,
                         urlparse('https://ascribe0.s3.amazonaws.com/local/testuser/'
                                  'ascribe_spiral/digitalwork/ascribe_spiral.png').path)
        self.assertEqual(urlparse(save_file.url_safe).path,
                         urlparse('https://ascribe0.s3.amazonaws.com/local%2Ftestuser%2F'
                                  'ascribe_spiral%2Fdigitalwork%2Fascribe_spiral.png').path)
        self.assertEqual(save_file.mime, "image")
        # self.assertEqual(save_file.associated_key(), 'local/testuser/ascribe_spiral/otherdata')

        find_file = DigitalWork.objects.get(digital_work_file=save_file.key)
        self.compare_file(save_file, find_file)
        self.assertEqual(save_file.hash, find_file.hash)

    def test_create_thumbnail(self):
        save_file = Thumbnail(user=self.user_test, key=FIX_KEY_PNG)
        save_file.save()
        find_file = Thumbnail.objects.get(thumbnail_file=save_file.key)
        self.compare_file(save_file, find_file)
        find_file = Thumbnail.objects.get(id=save_file.id)
        self.compare_file(save_file, find_file)

    def test_save_thumbnail_default(self):
        key = 'test/giftest/brainlarge.png'
        url = 'https://s3-us-west-2.amazonaws.com/ascribe0/{}'.format(key)
        thumbnail = Thumbnail(user=self.user_test,
                              thumbnail_file=settings.THUMBNAIL_DEFAULT,
                              thumbnail_sizes={})
        thumbnail.save()
        thumbnail = Thumbnail.thumbnail_from_url(url, key, thumbnail)
        test_cases = set(thumbnail.thumbnail_sizes.values())
        for t in test_cases:
            Image.open(urllib.urlretrieve(t)[0])

    def test_save_thumbnail_as_jpg(self):
        key = 'test/giftest/exifTest.jpg'
        url = 'https://s3-us-west-2.amazonaws.com/ascribe0/{}'.format(key)
        thumbnail = Thumbnail(user=self.user_test,
                              thumbnail_file=settings.THUMBNAIL_DEFAULT,
                              thumbnail_sizes={})
        thumbnail.save()
        thumbnail = Thumbnail.thumbnail_from_url(url, key, thumbnail)
        test_cases = set(thumbnail.thumbnail_sizes.values())
        for t in test_cases:
            Image.open(urllib.urlretrieve(t)[0])

    def test_save_bmp_as_jpeg_thumbnail(self):
        key = 'test/imagetests/lenna.bmp'
        url = 'https://s3-us-west-2.amazonaws.com/ascribe0/{}'.format(key)
        thumbnail = Thumbnail(user=self.user_test,
                              thumbnail_file=settings.THUMBNAIL_DEFAULT,
                              thumbnail_sizes={})
        thumbnail.save()
        thumbnail = Thumbnail.thumbnail_from_url(url, key, thumbnail)
        thumbnail_formats = [Image.open(urllib.urlretrieve(thumbnail_url)[0]).format for thumbnail_url
                             in thumbnail.thumbnail_sizes.values()]
        self.assertTrue(all(f == 'JPEG' for f in thumbnail_formats),
                        msg='All thumbnails of a BMP file must be of format JPEG')

    def test_save_gif_as_gif_thumbnail(self):
        key = 'test/imagetests/lenna.gif'
        url = 'https://s3-us-west-2.amazonaws.com/ascribe0/{}'.format(key)
        thumbnail = Thumbnail(user=self.user_test,
                              thumbnail_file=settings.THUMBNAIL_DEFAULT,
                              thumbnail_sizes={})
        thumbnail.save()
        thumbnail = Thumbnail.thumbnail_from_url(url, key, thumbnail)
        thumbnail_formats = [Image.open(urllib.urlretrieve(thumbnail_url)[0]).format for thumbnail_url
                             in thumbnail.thumbnail_sizes.values()]
        self.assertTrue(all(f == 'GIF' for f in thumbnail_formats),
                        msg='All thumbnails of a GIF file must be of format GIF')

    def test_save_jpeg_as_jpeg_thumbnail(self):
        key = 'test/imagetests/lenna.jpeg'
        url = 'https://s3-us-west-2.amazonaws.com/ascribe0/{}'.format(key)
        thumbnail = Thumbnail(user=self.user_test,
                              thumbnail_file=settings.THUMBNAIL_DEFAULT,
                              thumbnail_sizes={})
        thumbnail.save()
        thumbnail = Thumbnail.thumbnail_from_url(url, key, thumbnail)
        thumbnail_formats = [Image.open(urllib.urlretrieve(thumbnail_url)[0]).format for thumbnail_url
                             in thumbnail.thumbnail_sizes.values()]
        self.assertTrue(all(f == 'JPEG' for f in thumbnail_formats),
                        msg='All thumbnails of a JPEG file must be of format JPEG')

    def test_save_png_as_jpeg_thumbnail(self):
        key = 'test/imagetests/lenna.png'
        url = 'https://s3-us-west-2.amazonaws.com/ascribe0/{}'.format(key)
        thumbnail = Thumbnail(user=self.user_test,
                              thumbnail_file=settings.THUMBNAIL_DEFAULT,
                              thumbnail_sizes={})
        thumbnail.save()
        thumbnail = Thumbnail.thumbnail_from_url(url, key, thumbnail)
        thumbnail_formats = [Image.open(urllib.urlretrieve(thumbnail_url)[0]).format for thumbnail_url
                             in thumbnail.thumbnail_sizes.values()]
        self.assertTrue(all(f == 'JPEG' for f in thumbnail_formats),
                        msg='All thumbnails of a PNG file must be of format JPEG')

    def test_save_tiff_as_jpeg_thumbnail(self):
        key = 'test/imagetests/lenna.tiff'
        url = 'https://s3-us-west-2.amazonaws.com/ascribe0/{}'.format(key)
        thumbnail = Thumbnail(user=self.user_test,
                              thumbnail_file=settings.THUMBNAIL_DEFAULT,
                              thumbnail_sizes={})
        thumbnail.save()
        thumbnail = Thumbnail.thumbnail_from_url(url, key, thumbnail)
        thumbnail_formats = [Image.open(urllib.urlretrieve(thumbnail_url)[0]).format for thumbnail_url
                             in thumbnail.thumbnail_sizes.values()]
        self.assertTrue(all(f == 'JPEG' for f in thumbnail_formats),
                        msg='All thumbnails of a TIFF file must be of format JPEG')

    def test_save_tif_as_jpeg_thumbnail(self):
        key = 'test/imagetests/lenna.tif'
        url = 'https://s3-us-west-2.amazonaws.com/ascribe0/{}'.format(key)
        thumbnail = Thumbnail(user=self.user_test,
                              thumbnail_file=settings.THUMBNAIL_DEFAULT,
                              thumbnail_sizes={})
        thumbnail.save()
        thumbnail = Thumbnail.thumbnail_from_url(url, key, thumbnail)
        thumbnail_formats = [Image.open(urllib.urlretrieve(thumbnail_url)[0]).format for thumbnail_url
                             in thumbnail.thumbnail_sizes.values()]
        self.assertTrue(all(f == 'JPEG' for f in thumbnail_formats),
                        msg='All thumbnails of a TIF file must be of format JPEG')

    def test_resize_gif(self):
        key = 'test/giftest/ERuXtjY.gif'
        url = 'https://s3-us-west-2.amazonaws.com/ascribe0/{}'.format(key)
        thumbnail = Thumbnail(user=self.user_test,
                              thumbnail_file=settings.THUMBNAIL_DEFAULT,
                              thumbnail_sizes={})
        thumbnail.save()
        thumbnail = Thumbnail.thumbnail_from_url(url, key, thumbnail)
        test_cases = set(thumbnail.thumbnail_sizes.values())
        for t in test_cases:
            try:
                output_image = Image.open(urllib.urlretrieve(t)[0])
            except Exception, e:
                # Lol
                print 'Exception ... '
                raise AssertionError(e.args)
            try:
                output_image.seek(1)
            except:
                raise AssertionError('Gif is not animated')

    def test_create_other_data(self):
        save_file = OtherData(user=self.user_test, key=FIX_KEY_PNG)
        save_file.save()
        find_file = OtherData.objects.get(other_data_file=save_file.key)
        self.compare_file(save_file, find_file)

        find_file = OtherData.objects.get(id=save_file.id)
        self.compare_file(save_file, find_file)

    def test_assemble_key_with_unicode_filename(self):
        from ..models import Thumbnail
        user_id = 'dummy_user_id'
        category = 'dummy_category'
        filename = '比特币.jpg'
        key = Thumbnail._assemble_key(user_id, category, filename)
        self.assertEqual(key, u'{}/{}/{}/{}'.format(
            settings.DEPLOYMENT, user_id, category, filename.decode('utf-8')))

    def test_assemble_key_with_ascii_filename(self):
        from ..models import Thumbnail
        user_id = 'dummy_user_id'
        category = 'dummy_category'
        filename = 'bitcoin.jpg'
        key = Thumbnail._assemble_key(user_id, category, filename)
        self.assertEqual(key, '{}/{}/{}/{}'.format(
            settings.DEPLOYMENT, user_id, category, filename))
