from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView, RedirectView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt'), name='robots_txt'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^s3/', include('s3.urls', namespace='s3')),
    url(r'^encoder/', include('encoder.urls', namespace='encoder')),
    url(r'^api/', include('web.urls.api', namespace='api')),
)

#Accessing media files in django:
# Usually when in production, you want the webserver to serve static and media files.
# If developing, just get the django development server to serve them for you.
# To do this, tell it to route all incoming requests to http://mysite.com/media
# to MEDIA_ROOT and all requests to http://mysite.com/static to STATIC_ROOT.
# (From http://stackoverflow.com/questions/6418072/accessing-media-files-in-django1)

if settings.DEBUG or settings.DEPLOYMENT == 'staging':
    urlpatterns += patterns(
        '',
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT}),
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
        url(r'^api-auth/', include('rest_framework.urls',
                                   namespace='rest_framework')),
        )
