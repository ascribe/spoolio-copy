from rest_framework import routers

from api import UserEndpoint

router = routers.DefaultRouter()
router.register(r'users', UserEndpoint)
urlpatterns = router.urls
