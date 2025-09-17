from datetime import datetime
from django.db import models
from django.urls import reverse

from calendarapp.models import EventAbstract
from accounts.models import User
from django.utils import timezone
from calendarapp.models.car import Car  # adjust path if needed

class EventManager(models.Manager):
    """ Event manager """

    def get_all_events(self, user=None):
        filters = {
            'is_active': True,
            'is_deleted': False
        }
        if user:
            filters['user'] = user
        return Event.objects.filter(**filters)



    def get_running_events(self, user=None):
        now = timezone.now()
        filters = {
            'is_active': True,
            'is_deleted': False,
            'end_time__gte': now,
            'start_time__lte': now
        }
        if user:
            filters['user'] = user
        return Event.objects.filter(**filters).order_by("start_time")

    
    def get_completed_events(self, user=None):
        now = timezone.now()
        filters = {
            'is_active': True,
            'is_deleted': False,
            'end_time__lt': now
        }
        if user:
            filters['user'] = user
        return Event.objects.filter(**filters)
    
    def get_upcoming_events(self, user=None):
        now = timezone.now()
        filters = {
            'is_active': True,
            'is_deleted': False,
            'start_time__gt': now
        }
        if user:
            filters['user'] = user
        return Event.objects.filter(**filters)


class Event(EventAbstract):
    """ Event model """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    acknowledged = models.BooleanField(default=True)

    objects = EventManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("calendarapp:event-detail", args=(self.id,))

    @property
    def get_html_url(self):
        url = reverse("calendarapp:event-detail", args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'