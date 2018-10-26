from django.conf.urls import patterns, include, url
from rest_framework import routers

from whitelabel.ikonotv import api

router = routers.DefaultRouter()
router.register(r'/pieces', api.IkonotvPieceEndpoint)
router.register(r'/users', api.IkonotvUserEndpoint)
urlpatterns = router.urls


