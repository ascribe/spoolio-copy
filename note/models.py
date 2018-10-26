from django.contrib.auth.models import User
from django.db import models


class Note(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='note_at_user', null=True)
    edition = models.ForeignKey("piece.Edition", related_name='note_at_edition', blank=True, null=True)
    piece = models.ForeignKey("piece.Piece", related_name='note_at_piece', blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True)

    @classmethod
    def create(cls, owner, edition, note):
        note = cls(user=owner, edition=edition, note=note)
        note.type = cls.__name__
        return note

    @property
    def gettype(self):
        return self.__class__.__name__

    def __unicode__(self):
        return unicode(self.note)


class PrivateNoteManager(models.Manager):
    """ Manager for PublicEditionNote """
    def get_queryset(self):
        return super(PrivateNoteManager, self).get_queryset().filter(type='PrivateNote')


class PrivateNote(Note):
    objects = PrivateNoteManager()

    class Meta:
        proxy = True


class PublicNoteManager(models.Manager):
    """ Manager for PublicEditionNote """
    def get_queryset(self):
        return super(PublicNoteManager, self).get_queryset().filter(type='PublicNote')


class PublicNote(PrivateNote):

    objects = PublicNoteManager()

    class Meta:
        proxy = True

