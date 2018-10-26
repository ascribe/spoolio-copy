from rest_framework import routers

from blobs import api as file_api

router = routers.DefaultRouter()
router.register(r'/thumbnails', file_api.ThumbnailEndpoint )
router.register(r'/otherdatas', file_api.OtherDataEndpoint )
router.register(r'/digitalworks', file_api.DigitalWorkEndpoint )
router.register(r'/contracts', file_api.ContractBlobEndpoint )
urlpatterns = router.urls


