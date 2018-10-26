from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'^', include('applications.urls', namespace='applications')),
    # TODO put a namespace for pieces as well
    url(r'^', include('piece.urls')),
    url(r'^', include('users.urls', namespace='users')),
    url(r'^', include('prize.urls', namespace='prize')),
    url(r'^blob', include('blobs.urls', namespace='blob')),
    url(r'^coa', include('coa.urls', namespace='coa')),
    url(r'^note', include('note.urls', namespace='note')),
    url(r'^notifications', include('notifications.urls', namespace='notifications')),
    url(r'^bitcoin', include('bitcoin.urls', namespace='bitcoin')),
    url(r'^ownership', include('ownership.urls', namespace='ownership')),
    url(r'^webhooks', include('webhooks.urls', namespace='webhooks')),
    url(r'^whitelabel', include('whitelabel.urls', namespace='whitelabel'))
]
