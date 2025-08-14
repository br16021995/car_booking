from django.contrib import admin
from calendarapp import models
from calendarapp.models import Car

@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    model = models.Event
    list_display = [
        "id",
        "title",
        "user",
        "is_active",
        "is_deleted",
        "created_at",
        "updated_at",
    ]
    list_filter = ["is_active", "is_deleted"]
    search_fields = ["title"]


@admin.register(models.EventMember)
class EventMemberAdmin(admin.ModelAdmin):
    model = models.EventMember
    list_display = ["id", "event", "user", "created_at", "updated_at"]
    list_filter = ["event"]


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    model = Car
    list_display = ["id", "car_name", "car_unique_id", "date", "updated_date", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["car_name", "car_unique_id"]