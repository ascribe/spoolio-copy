from django.conf import settings
from django.test import TestCase

import boto

from moto import mock_s3


class MockAwsTestCase(TestCase):

    def setUp(self):
        self.mock = mock_s3()
        self.mock.start()
        self.s3_connection = boto.connect_s3()
        self.bucket = self.s3_connection.create_bucket(
            settings.AWS_STORAGE_BUCKET_NAME)

    def tearDown(self):
        self.mock.stop()
