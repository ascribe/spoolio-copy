"""Utility models."""
from django.contrib.auth.models import User
from django.db import models


class JobMonitor(models.Model):
    """Job monitoring class.

    Attributes:
        description (django.db.models.CharField): Description. E.g.:
        ``'bitcoin tx'``, ``'convert video'``,
        ``'upload aws'``, ``'send mail'``.

        object_id (django.db.models.CharField): Object ID.

        resource_id (django.db.models.CharField): Resource ID.

        percent_done (django.db.models.IntegerField): Percentage of
        the job that is done.

        user (django.contrib.auth.models.User): User.

        created (django.db.models.DateTimeField): Creation timestamp.

    """
    description = models.CharField(max_length=25)
    object_id = models.CharField(max_length=160)
    resource_id = models.CharField(max_length=160, default='0')
    percent_done = models.IntegerField()
    user = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)


class BackendException(models.Model):

    type = models.CharField(max_length=100)
    value = models.CharField(max_length=400)
    traceback = models.TextField()

    datetime = models.DateTimeField(auto_now_add=True)
