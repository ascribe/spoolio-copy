from rest_framework import routers

from . import api

router = routers.SimpleRouter()
router.register(r'', api.HookViewSet, 'webhook')

urlpatterns = router.urls
