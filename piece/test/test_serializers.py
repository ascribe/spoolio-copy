# coding=utf-8
"""
Serializer tests
"""

from django.test import TestCase

from piece.serializers import PieceForm


# Test fields
class PieceFormSerializerTest(TestCase):
    fixtures = ['licenses.json']

    def testFields(self):
        serializer = PieceForm(data={})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'digital_work_key': [u'This field is required.'],
                                             'artist_name': [u'This field is required.'],
                                             'title': [u'This field is required.']})

    def testDateCreatedRange(self):
        data = {'digital_work_key': 'key',
                'artist_name': 'artist',
                'title': 'title',
                'license': 'default',
                'date_created': 1}

        serializer = PieceForm(data=data)
        self.assertTrue(serializer.is_valid())

        # test negative year
        data.update({'date_created': -1})
        serializer = PieceForm(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('date_created', serializer.errors.keys())

        # test zero year
        data.update({'date_created': 0})
        serializer = PieceForm(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('date_created', serializer.errors.keys())


    def testThumbnailExists(self):
        data = {'digital_work_key': 'key',
            'artist_name': 'artist',
            'title': 'title',
            'license': 'default',
            'date_created': 1,
            'thumbnail_file': 'media/thumbnails/ascribe_spiral.png'}

        serializer = PieceForm(data=data)
        self.assertTrue(serializer.is_valid())