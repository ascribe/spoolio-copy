from rest_framework import routers

from note import api as note_api

router = routers.DefaultRouter()
router.register(r'/private/editions', note_api.NoteEndpoint)
router.register(r'/private/pieces', note_api.NotePieceEndpoint)
router.register(r'/public/editions', note_api.PublicEditionNoteEndpoint)
router.register(r'/public/pieces', note_api.PublicPieceNoteEndpoint)
urlpatterns = router.urls
