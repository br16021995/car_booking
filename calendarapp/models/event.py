from datetime import datetime
from django.db import models
from django.urls import reverse

from calendarapp.models import EventAbstract
from accounts.models import User
from django.utils import timezone


class EventManager(models.Manager):
    """ Event manager """

    def get_all_events(self, user):
        events = Event.objects.filter(user=user, is_active=True, is_deleted=False)
        return events



    def get_running_events(self, user):
        now = timezone.now()
        running_events = Event.objects.filter(
            user=user,
            is_active=True,
            is_deleted=False,
            end_time__gte=now,
            start_time__lte=now
        ).order_by("start_time")
        return running_events

    
    def get_completed_events(self, user):
        now = timezone.now()
        completed_events = Event.objects.filter(
            user=user,
            is_active=True,
            is_deleted=False,
            end_time__lt=now,
        )
        return completed_events
    
    def get_upcoming_events(self, user):
        now = timezone.now()
        upcoming_events = Event.objects.filter(
            user=user,
            is_active=True,
            is_deleted=False,
            start_time__gt=now,
        )
        return upcoming_events


class Event(EventAbstract):
    """ Event model """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    objects = EventManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("calendarapp:event-detail", args=(self.id,))

    @property
    def get_html_url(self):
        url = reverse("calendarapp:event-detail", args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'