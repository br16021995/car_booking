# calendarapp/models.py

from django.db import models

class VehicleProgram(models.Model):
    name = models.CharField(max_length=150, unique=True)   # required field
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name