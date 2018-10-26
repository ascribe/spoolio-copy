from django.contrib.auth.models import User
from django.db import models

from jsonfield import JSONField

from acl.models import ActionControlFieldsMixin, UserActionControlFieldsMixin


class WhitelabelActionControlMixin(models.Model):

    acl_wallet_submit = models.BooleanField(default=False)
    acl_wallet_submitted = models.BooleanField(default=False)
    acl_wallet_accepted = models.BooleanField(default=False)

    acl_view_powered_by = models.BooleanField(default=False)
    acl_view_settings_copyright_association = models.BooleanField(default=False)

    class Meta:
        abstract = True


class WhitelabelSettings(ActionControlFieldsMixin,
                         UserActionControlFieldsMixin,
                         WhitelabelActionControlMixin,
                         models.Model):

    user = models.ForeignKey(User)
    subdomain = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    logo = models.URLField(max_length=1000)
    head = JSONField(null=True, blank=True)
    title = models.CharField(blank=True, max_length=20)

    def __unicode__(self):
        return unicode(self.subdomain)
