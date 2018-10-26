# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def test_rotate_jpg_from_exif(monkeypatch):
    from ..image import rotate_jpg_from_exif, EXIF_IMAGE_ORIENTATION

    class ImageMock(object):

        def _getexif(self):
            return {EXIF_IMAGE_ORIENTATION: 'k'}

    image_mock = ImageMock()
    assert rotate_jpg_from_exif(image_mock) == image_mock
