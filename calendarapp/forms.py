from django.forms import ModelForm, DateInput
from calendarapp.models import Event, EventMember
from django import forms
from datetime import datetime, timedelta


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "start_time", "end_time"]
        # datetime-local is a HTML5 input type
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter event title"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter event description",
                }
            ),
            "start_time": DateInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_time": DateInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
        }
        exclude = ["user"]

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        # input_formats to parse HTML5 datetime-local input to datetime field
        self.fields["start_time"].input_formats = ("%Y-%m-%dT%H:%M",)
        self.fields["end_time"].input_formats = ("%Y-%m-%dT%H:%M",)

        # Set min/max for 3 months window
        now = datetime.now()
        min_date = now.strftime("%Y-%m-%dT%H:%M")
        max_date = (now + timedelta(days=90)).strftime("%Y-%m-%dT%H:%M")

        self.fields["start_time"].widget.attrs["min"] = min_date
        self.fields["start_time"].widget.attrs["max"] = max_date
        self.fields["end_time"].widget.attrs["min"] = min_date
        self.fields["end_time"].widget.attrs["max"] = max_date


class AddMemberForm(forms.ModelForm):
    class Meta:
        model = EventMember
        fields = ["user"]
