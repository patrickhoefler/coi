from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField
from django_mongodb_engine.contrib import MongoDBManager


class Activities(models.Model):
    id = models.CharField(primary_key=True, max_length=1024)
    displayName = models.TextField()
    image  = models.TextField()
    score_list = ListField(models.IntegerField())
    score_list_24 = ListField(models.IntegerField())
    score = models.IntegerField()
    score_24 = models.IntegerField()
    updated = models.DateTimeField()

class Post(models.Model):
    id = models.CharField(primary_key=True, max_length=1024)
    title = models.TextField()
    content = models.TextField(null=True)
    image = models.TextField()
    url = models.TextField()
    actorId = models.TextField()
    actorDisplayName = models.TextField()
    actorImage  = models.TextField()
    published = models.DateTimeField()
    number_of_plusoners = models.IntegerField()
    number_of_replies = models.IntegerField()
    number_of_resharers = models.IntegerField()
    score = models.IntegerField()
    updated = models.DateTimeField()
