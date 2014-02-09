from django.conf.urls import patterns, url

urlpatterns = patterns('electionapp.views',
	url(r'^$', 			'index'),
	url(r'^about/$', 	'about'),
	url(r'^systems/$', 	'systems'),
	url(r'^create/$', 	'create'),
	url(r'^dashboard/$', 'dashboard'),
	url(r'^account/$', 	'account'),
	url(r'^(\w+)/$', 'analyze_key'),
)