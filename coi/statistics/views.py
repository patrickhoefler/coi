import datetime
from django.views.generic import ListView, DetailView
from django.http import Http404
from statistics.models import Activities, Post


class FrontPageView(ListView):
    queryset = Activities.objects.all().order_by('-score')[:100]
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(FrontPageView, self).get_context_data(**kwargs)
        # Add in the publisher
        context['posts_list'] = Post.objects.all().order_by('-score')[:100]
        context['activities_list_24'] = Activities.objects.all().order_by('-score_24')[:10]
        context['posts_list_24'] = Post.objects.filter(published__gt=(datetime.datetime.utcnow()-datetime.timedelta(days=1))).order_by('-score')[:10]
        return context


class PersonDetailView(ListView):
    template_name = 'person.html'

    def get_queryset(self):
        try:
            my_object = Activities.objects.get(pk=self.args[0])
        except Activities.DoesNotExist:
            raise Http404

        return Post.objects.filter(actorId=self.args[0])

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PersonDetailView, self).get_context_data(**kwargs)
        # Add in the publisher
        context['posts_list'] = Post.objects.all().order_by('-score')[:100]
        context['activities_list_24'] = Activities.objects.all().order_by('-score_24')[:10]
        context['posts_list_24'] = Post.objects.filter(published__gt=(datetime.datetime.utcnow()-datetime.timedelta(days=1))).order_by('-score')[:10]
        return context
