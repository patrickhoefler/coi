from django.conf.urls import *
from cache.views import QueueView
from statistics.views import FrontPageView, PersonDetailView

urlpatterns = patterns('',
    (r'^$', FrontPageView.as_view()),
    (r'^(\d+)', PersonDetailView.as_view()),
    (r'^queue', QueueView.as_view()),
)
