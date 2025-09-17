# cal/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.views import generic
from django.utils.safestring import mark_safe
from datetime import timedelta, datetime, date
import calendar
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib import messages
from calendarapp.models import VehicleProgram
from calendarapp.utils import send_booking_email
from accounts.models import User





from calendarapp.models import EventMember, Event,Car
from calendarapp.utils import Calendar
from calendarapp.forms import EventForm, AddMemberForm


def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split("-"))
        return date(year, month, day=1)
    return datetime.today()


def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = "month=" + str(prev_month.year) + "-" + str(prev_month.month)
    return month


def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = "month=" + str(next_month.year) + "-" + str(next_month.month)
    return month


class CalendarView(LoginRequiredMixin, generic.ListView):
    login_url = "accounts:signin"
    model = Event
    template_name = "calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        d = get_date(self.request.GET.get("month", None))
        cal = Calendar(d.year, d.month)
        html_cal = cal.formatmonth(withyear=True)
        context["calendar"] = mark_safe(html_cal)
        context["prev_month"] = prev_month(d)
        context["next_month"] = next_month(d)
        return context


@login_required(login_url="signup")
def create_event(request):
    # You might want to update this view as well if it's still in use
    # to pass the user to the form, similar to CalendarViewNew.
    form = EventForm(request.POST or None, user=request.user) # <--- ADD user=request.user
    if request.POST and form.is_valid():
        title = form.cleaned_data["title"]
        description = form.cleaned_data["description"]
        start_time = form.cleaned_data["start_time"]
        end_time = form.cleaned_data["end_time"]
        Event.objects.get_or_create(
            user=request.user,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
        )
        return HttpResponseRedirect(reverse("calendarapp:calendar"))
    return render(request, "event.html", {"form": form})


class EventEdit(generic.UpdateView):
    model = Event
    fields = ["title", "description", "start_time", "end_time"]
    template_name = "event.html"

    # Override get_form_kwargs to pass the user to the form
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


@login_required(login_url="signup")
def event_details(request, event_id):
    event = Event.objects.get(id=event_id)
    eventmember = EventMember.objects.filter(event=event)
    context = {"event": event, "eventmember": eventmember}
    return render(request, "event-details.html", context)


def add_eventmember(request, event_id):
    forms = AddMemberForm()
    if request.method == "POST":
        forms = AddMemberForm(request.POST)
        if forms.is_valid():
            member = EventMember.objects.filter(event=event_id)
            event = Event.objects.get(id=event_id)
            if member.count() <= 9:
                user = forms.cleaned_data["user"]
                EventMember.objects.create(event=event, user=user)
                return redirect("calendarapp:calendar")
            else:
                print("--------------User limit exceed!-----------------")
    context = {"form": forms}
    return render(request, "add_member.html", context)


class EventMemberDeleteView(generic.DeleteView):
    model = EventMember
    template_name = "event_delete.html"
    success_url = reverse_lazy("calendarapp:calendar")

class CalendarViewNew(LoginRequiredMixin, generic.View):
    login_url = "accounts:signin"
    template_name = "calendarapp/calendar.html"
    form_class = EventForm

    def get(self, request, *args, **kwargs):
        forms = self.form_class(user=request.user)
        vehicle_programs = VehicleProgram.objects.filter(is_active=True).prefetch_related('cars')
        car_id = request.GET.get('car_id')
        events = Event.objects.none()
        events_month = Event.objects.none()

        selected_car = None
        if car_id:
            try:
                selected_car = Car.objects.get(id=car_id)
                now = timezone.now()
                events = Event.objects.filter(car=selected_car, is_active=True)
                events_month = events.filter(end_time__gte=now, start_time__lte=now)
            except Car.DoesNotExist:
                selected_car = None

        event_list = []
        for event in events:
            event_list.append({
                "id": event.id,
                "title": event.title,
                "start": event.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": event.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "description": event.description,
                "car_name": event.car.car_name + " - ( " + event.car.car_unique_id + " )",
                "car_id": event.car.id,
                "booked_by": f"{event.user.first_name} {event.user.last_name}".strip(),
                "user_id": event.user.id,
            })

        is_admin = request.user.is_staff or request.user.is_superuser
        # Calculate available cars for today
        today = timezone.now()
        print('hidf')
        print(today)
        available_cars_today = set(Car.objects.filter(is_active=True).values_list('id', flat=True))
        booked_cars_today = set(Event.objects.filter(
            is_active=True,
            start_time__date__lte=today,
            end_time__date__gte=today
        ).values_list('car_id', flat=True))
        available_cars_today -= booked_cars_today


        context = {
            "form": forms,
            "vehicle_programs": vehicle_programs,
            "selected_car": selected_car,
            "events": event_list,
            "events_month": events_month,
            "is_admin": is_admin,
            "available_cars_today": available_cars_today,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, user=request.user)
        cars = Car.objects.filter(is_active=True)
        vehicle_programs = VehicleProgram.objects.filter(is_active=True).prefetch_related('cars')

        car_id = request.POST.get('car') or request.GET.get('car_id')
        selected_car = None
        if car_id:
            try:
                selected_car = cars.get(id=car_id)
            except Car.DoesNotExist:
                selected_car = None

        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user

            duration = event.end_time - event.start_time
            max_days = 30 if (request.user.is_superuser or request.user.is_staff) else 4

            if duration > timedelta(days=max_days):
                messages.error(request, f"You cannot book car for more than {max_days} days.")
                return redirect(f"{reverse('calendarapp:calendar')}?car_id={car_id}")

            overlapping_events = Event.objects.filter(
                user=request.user,
                is_active=True,
                start_time__lt=event.end_time,
                end_time__gt=event.start_time
            ).exclude(car=selected_car)

            if overlapping_events.exists():
                messages.error(request, "You already have a booking for another car during this time slot.")
                return redirect(f"{reverse('calendarapp:calendar')}?car_id={car_id}")

            event.save()
            # Inside CalendarViewNew.post after event.save()
            user_email = request.user.email
            user_name = f"{request.user.first_name} {request.user.last_name}".strip()
            car_name = event.car.car_name
            start_time = event.start_time.strftime("%Y-%m-%d %H:%M")
            end_time = event.end_time.strftime("%Y-%m-%d %H:%M")

            send_booking_email(user_email, user_name, car_name, start_time, end_time)
            messages.success(request, "Car booked successfully!")
            return redirect(f"{reverse('calendarapp:calendar')}?car_id={car_id}" if car_id else "calendarapp:calendar")

        # === If form is invalid, re-render page with full context ===
        now = timezone.now()
        events = Event.objects.filter(car=selected_car, is_active=True) if selected_car else Event.objects.none()
        events_month = events.filter(end_time__gte=now, start_time__lte=now)

        event_list = []
        for event in events:
            event_list.append({
                "id": event.id,
                "title": event.title,
                "start": event.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": event.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "description": event.description,
                "car_name": event.car.car_name + " - ( " + event.car.car_unique_id + " )",
                "car_id": event.car.id,
                "booked_by": f"{event.user.first_name} {event.user.last_name}".strip(),
                "user_id": event.user.id,
            })

        is_admin = request.user.is_staff or request.user.is_superuser
        today = timezone.now()
        available_cars_today = set(Car.objects.filter(is_active=True).values_list('id', flat=True))
        booked_cars_today = set(Event.objects.filter(
            is_active=True,
            start_time__date__lte=today,
            end_time__date__gte=today
        ).values_list('car_id', flat=True))
        available_cars_today -= booked_cars_today

        context = {
            "form": form,
            "vehicle_programs": vehicle_programs,
            "selected_car": selected_car,
            "events": event_list,
            "events_month": events_month,
            "is_admin": is_admin,
            "available_cars_today": available_cars_today,
        }

        return render(request, self.template_name, context)



def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        # <--- ADD THIS CHECK
        if request.user == event.user or request.user.is_superuser or request.user.is_staff: # Allow superuser/staff to delete
            event.delete()
            return JsonResponse({'message': 'Event successfully deleted.'})
        else:
            return JsonResponse({'message': 'You are not authorized to delete this event.'}, status=403) # Forbidden
    else:
        return JsonResponse({'message': 'Invalid request method.'}, status=400)

def next_week(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        next = event
        next.id = None
        next.start_time += timedelta(days=7)
        next.end_time += timedelta(days=7)
        next.save()
        return JsonResponse({'message': 'Sucess!'})
    else:
        return JsonResponse({'message': 'Error!'}, status=400)

def next_day(request, event_id):

    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        next = event
        next.id = None
        next.start_time += timedelta(days=1)
        next.end_time += timedelta(days=1)
        next.save()
        return JsonResponse({'message': 'Sucess!'})
    else:
        return JsonResponse({'message': 'Error!'}, status=400)
    

def acknowledge_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user == event.user or request.user.is_superuser or request.user.is_staff:
        if event.acknowledged != True:
            event.acknowledged = True
            event.save()
            return JsonResponse({'message': 'Event acknowledged successfully.'})
        else:
            return JsonResponse({'message': 'Event already acknowledged successfully.'})

    else:
        return JsonResponse({'message': 'You are not authorized to acknowledge this event.'}, status=403)