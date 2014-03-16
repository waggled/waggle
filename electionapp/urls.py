from django.conf.urls import patterns, url

urlpatterns = patterns('electionapp.views',
	url(r'^$', 			'index'),
    url(r'^polls/$',    'polls_overview'),
    url(r'^users/$',    'users_overview'),
    url(r'^login/$', 'login'),
    url(r'^logout/$', 'logout'),
	url(r'^about/$', 	'about'),
	url(r'^systems/$', 	'systems'),
	url(r'^create/$', 	'create'),
	url(r'^dashboard/$', 'dashboard'),
	url(r'^account/$', 	'account'),
    url(r'^(\w+)/$', 'analyze_key'),
    url(r'^(\w+)/close/$', 'close_election'),
    url(r'^(\w+)/edit/$', 'edit_vote'),
    url(r'^(\w+)/close/(\w+)$', 'close_election'), #dev only
    url(r'^vote/$', 'vote'),
)