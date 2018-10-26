from django.conf.urls import patterns, include, url

import encoder.views as views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'python_django_s3.views.home', name='home'),
    # url(r'^python_django_s3/', include('python_django_s3.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(r'^notifications_handler/', views.notifications_handler, name="upload_s3_multi_sign"),
)
