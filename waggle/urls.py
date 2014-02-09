from django.conf.urls import patterns, include, url

#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
	url('', include('electionapp.urls')),
)

handler404 = 'electionapp.views.custom_404'