import ast

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

from note.models import PrivateNote
from piece.models import Piece
from whitelabel.models import WhitelabelSettings


class Prize(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)

    rounds = models.IntegerField(default=1, null=False)
    active_round = models.IntegerField(default=1, blank=True, null=True)
    active = models.BooleanField(default=False, null=False)
    num_submissions = models.IntegerField(blank=True, null=True)
    whitelabel_settings = models.ForeignKey(WhitelabelSettings, null=True)

    @property
    def subdomain(self):
        return self.whitelabel_settings.subdomain

    @property
    def name(self):
        if self.whitelabel_settings:
            return self.whitelabel_settings.name
        else:
            return ''

    def __unicode__(self):
        return self.name


class PrizeUser(models.Model):
    user = models.ForeignKey(User)
    prize = models.ForeignKey(Prize)
    # for inviting juries
    is_admin = models.BooleanField(default=False)
    # for jury members that can rate and take notes
    is_jury = models.BooleanField(default=False)
    # for shortlisting
    is_judge = models.BooleanField(default=False)
    round = models.IntegerField(blank=True, default=0)
    datetime_deleted = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("prize", "user", "is_jury", "round")

    def delete_safe(self):
        self.datetime_deleted = timezone.now()
        self.save()


class PrizePiece(models.Model):
    user = models.ForeignKey(User)
    piece = models.ForeignKey(Piece)
    prize = models.ForeignKey(Prize)
    # TODO: Change to JSONField data structure (dict-like structure)
    extra_data = models.TextField(blank=True, default="")
    is_selected = models.BooleanField(default=False, blank=True)
    round = models.IntegerField(blank=True, null=True, default=1)
    average_rating = models.FloatField(default=None, blank=True, null=True)
    num_ratings = models.IntegerField(default=None, blank=True, null=True)

    def set_average(self):
        ratings = Rating.objects.filter(piece=self.piece, type="Rating")
        self.average_rating = Rating.average(ratings)
        self.num_ratings = len(ratings)
        self.save()


class PieceAtPrize(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)

    piece = models.ForeignKey("piece.Edition")
    prize = models.ForeignKey(Prize)
    round = models.IntegerField(blank=True, null=True)
    extra_data_str = models.TextField(blank=True, default="")

    @property
    def extra_data(self):
        return ast.literal_eval(self.extra_data_str)

    @extra_data.setter
    def extra_data(self, value):
        self.extra_data_str = str(value)

    def export(self):
        from piece.serializers import PieceSerializer

        data = PieceSerializer(self.piece).data
        data.update({'prizeDetails': self.extra_data})
        return data


class RatingManager(models.Manager):
    """ Manager for Rating """

    def get_queryset(self):
        return super(RatingManager, self).get_queryset().filter(type='Rating')


class Rating(PrivateNote):
    objects = RatingManager()

    class Meta:
        proxy = True

    _rating = None

    @property
    def rating(self):
        if self.note:
            return float(self.note)
        return None

    @rating.setter
    def rating(self, value):
        self.note = str(value)

    @staticmethod
    def average(obj):
        if len(obj) == 0:
            return None
        ratings = [float(r.note) for r in obj]
        return sum(ratings) / len(ratings)
