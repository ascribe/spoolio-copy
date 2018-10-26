from rest_framework import routers

from api import ApplicationEndpoint

router = routers.DefaultRouter()
router.register(r'applications', ApplicationEndpoint)
urlpatterns = router.urls
