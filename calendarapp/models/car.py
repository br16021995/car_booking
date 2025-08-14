from django.db import models


class Car(models.Model):
    car_name = models.CharField(max_length=100)
    car_unique_id = models.SlugField(unique=True)
    date = models.DateField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.car_name