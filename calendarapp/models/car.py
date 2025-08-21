from django.db import models
from calendarapp.models.vehicleprogram import VehicleProgram

class Car(models.Model):
    car_name = models.CharField(max_length=100)
    car_unique_id = models.SlugField(unique=True)
    vehicle_program = models.ForeignKey(
        "calendarapp.VehicleProgram",
        on_delete=models.CASCADE,
        null=True,  # <-- allow null temporarily
        blank=True
    )
    vehicle_program = models.ForeignKey(VehicleProgram, on_delete=models.SET_NULL, null=True, blank=True, related_name='cars')
    date = models.DateField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.car_name
    
