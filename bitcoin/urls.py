from django.conf.urls import url

from bitcoin import api


urlpatterns = [
    url(r'confirmations/$', api.BitcoinNewBlockEndpoint.as_view(), name='confirmations'),
]
