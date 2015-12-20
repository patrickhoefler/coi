from django.db import models
from djangotoolbox.fields import ListField, EmbeddedModelField
from django_mongodb_engine.contrib import MongoDBManager

class Activity(models.Model):
    title = models.TextField()
    kind = models.TextField()
    published = models.DateTimeField()
    verb = models.TextField()
    actor = EmbeddedModelField('ActivityActor')
    object = EmbeddedModelField('ActivityObject')
    objects = MongoDBManager()

    def __unicode__(self):
        return self.title

class ActivityActor(models.Model):
    displayName = models.TextField()
    url = models.TextField()
    image = EmbeddedModelField('Image')

    def __unicode__(self):
        return self.displayName

class Image(models.Model):
    url = models.TextField()
    type = models.TextField()
    height = models.IntegerField()
    width = models.IntegerField()


class ActivityObject(models.Model):
    actor = EmbeddedModelField('ActivityActor')
    attachments = ListField(EmbeddedModelField('ObjectAttachment'))
    resharers = EmbeddedModelField('ObjectResharers')
    plusoners = EmbeddedModelField('ObjectPlusoners')
    replies = EmbeddedModelField('ObjectReplies')
    url = models.TextField()
    content = models.TextField()
    objectType = models.TextField()

class ObjectResharers(models.Model):
    totalItems = models.IntegerField()

class ObjectPlusoners(models.Model):
    totalItems = models.IntegerField()

class ObjectReplies(models.Model):
    totalItems = models.IntegerField()

class ObjectAttachment(models.Model):
    content = models.TextField()
    url = models.TextField()
    image = EmbeddedModelField('Image')
    fullImage = EmbeddedModelField('Image')
    objectType = models.TextField()
    displayName = models.TextField()

class Meta(models.Model):
    id = models.CharField(primary_key=True, max_length=1024)
    displayName = models.TextField()
    activities_crawled = models.DateTimeField()

class Queue(models.Model):
    displayName = models.TextField()
    priority = models.IntegerField()
    crawl_not_before = models.DateTimeField()
