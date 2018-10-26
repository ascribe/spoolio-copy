# coding=utf-8
"""
Serializer tests
"""

from django.test import TestCase


# Test fields
# Test password size
# Test password confirm
# Test unicode password
from blobs.serializers import DigitalWorkForm


class DigitalWorkSerializerTest(TestCase):

    def testFields(self):
        serializer = DigitalWorkForm(data={})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'digital_work_file': [u'This field is required.']})

    def testDigitalWorkMaxLength(self):
        serializer = DigitalWorkForm(data={'digital_work_file': '1234567890'*201})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['digital_work_file'],
                         [u'Ensure this field has no more than 2000 characters.'])


class ThumbnailSerializerTest(TestCase):

    pass