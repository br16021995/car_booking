from django.forms import ModelForm, DateInput
from calendarapp.models import Event, EventMember,Car
from accounts.models import User
from django import forms
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "start_time", "end_time", "car"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter event title"}
            ),
            "description": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter event description"},
            ),
            "start_time": DateInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_time": DateInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            # "car": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        # Extract the 'user' from kwargs before calling super()
        user = kwargs.pop('user', None)
        super(EventForm, self).__init__(*args, **kwargs)

        self.fields["start_time"].input_formats = ("%Y-%m-%dT%H:%M",)
        self.fields["end_time"].input_formats = ("%Y-%m-%dT%H:%M",)
        self.fields["car"].queryset = Car.objects.filter(is_active=True)

        now = datetime.now()
        min_date = now.strftime("%Y-%m-%dT%H:%M")

        # Determine max_delta_days based on user type
        if user and user.is_superuser:
            max_delta_days = 90
        else:
            max_delta_days = 30

        max_date = (now + timedelta(days=max_delta_days)).strftime("%Y-%m-%dT%H:%M")

        self.fields["start_time"].widget.attrs["min"] = min_date
        self.fields["start_time"].widget.attrs["max"] = max_date
        self.fields["end_time"].widget.attrs["min"] = min_date
        self.fields["end_time"].widget.attrs["max"] = max_date

    def clean(self):
        cleaned_data = super().clean()
        car = cleaned_data.get("car")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if not car or not start_time or not end_time:
            return cleaned_data  # Let other validators handle required fields

        # Find conflicting events
        conflicts = Event.objects.filter(
            car=car,
            is_active=True,
            is_deleted=False,
        ).exclude(id=self.instance.id if self.instance else None).filter(
            start_time__lt=end_time,
            end_time__gt=start_time,
        )

        if conflicts.exists():
            conflict_event = conflicts.first()
            booked_user = conflict_event.user
            raise ValidationError(
            f"The car '{car.car_name}' is already booked by {booked_user.first_name} {booked_user.last_name} "
            f"from {conflict_event.start_time.strftime('%Y-%m-%d %H:%M')} to {conflict_event.end_time.strftime('%Y-%m-%d %H:%M')}."
        )

        return cleaned_data


class AddMemberForm(forms.ModelForm):
    class Meta:
        model = EventMember
        fields = ["user"]