from rest_framework import routers
from coa.api import CoaEndpoint

router = routers.DefaultRouter()
router.register(r'', CoaEndpoint)
urlpatterns = router.urls
