from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Passwordresetcodes(models.Model):
    code = models.CharField(max_length=32)
    email = models.CharField(max_length = 120)
    time = models.DateTimeField()
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50) #TODO: do not save password

class Task(models.Model):
    STATUSES = (
        ('A', 'Active'),
        ('P', 'Pending'),
        ('W', 'Waiting'),
        ('D', 'Done'),
        ('C', 'Canceled'),
    )
#    def __str__(self):              # __unicode__ on Python 2
    def __unicode__(self):              # __unicode__ on Python 2
        return self.text
    user = models.ForeignKey(User)
    text = models.CharField(max_length=400)
    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=1, default='W', choices=STATUSES)
    createdate = models.DateTimeField('create date', blank=True, null=True)
    duedate = models.DateTimeField('due date', blank=True, null=True)
    actiondate = models.DateTimeField('action date', blank=True, null=True)
    mothertask = models.ForeignKey('Task', blank=True, default='', null=True)
