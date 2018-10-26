from django.conf.urls import patterns, include, url
from rest_framework import routers

from whitelabel.cyland import api

router = routers.DefaultRouter()
router.register(r'/pieces', api.CylandPieceEndpoint)
router.register(r'/users', api.CylandUserEndpoint)
urlpatterns = router.urls


