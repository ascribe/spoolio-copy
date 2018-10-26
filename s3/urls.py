from django.conf.urls import patterns, url

import s3.views as views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^signature', views.handle_s3, name="s3_sign"),
    url(r'^delete', views.handle_s3, name='s3_delete'),
    url(r'^success', views.success_redirect_endpoint, name="s3_succes_endpoint"),
    url(r'^key/$', views.create_key, name='key'),
    url(r'^sign_url/$', views.sign_url, name='sign_url'),
)
