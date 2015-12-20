import datetime
from django.views.generic import ListView, DetailView
from django.http import Http404
from cache.models import Queue


class QueueView(ListView):
    queryset = Queue.objects.all().order_by('-priority')[:500]
    template_name = 'queue.html'
