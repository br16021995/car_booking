# calendarapp/utils.py
from calendar import HTMLCalendar
from .models import Event

from accounts.models import User
from django.conf import settings
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events):
        events_per_day = events.filter(start_time__day=day)
        d = ""
        for event in events_per_day:
            d += f"<li> {event.get_html_url} </li>"
        if day != 0:
            return f"<td><span class='date'>{day}</span><ul> {d} </ul></td>"
        return "<td></td>"

    # formats a week as a tr
    def formatweek(self, theweek, events):
        week = ""
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f"<tr> {week} </tr>"

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, withyear=True):
        events = Event.objects.filter(
            start_time__year=self.year, start_time__month=self.month
        )
        cal = (
            '<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        )  # noqa
        cal += (
            f"{self.formatmonthname(self.year, self.month, withyear=withyear)}\n"
        )  # noqa
        cal += f"{self.formatweekheader()}\n"
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f"{self.formatweek(week, events)}\n"
        return cal




def send_booking_email(user_email, user_name, car_name, start_time, end_time):
    sender_email = settings.EMAIL_HOST_USER  # Use Django settings for email credentials
    password = settings.EMAIL_HOST_PASSWORD

    # Get all super admin emails
    super_admins = User.objects.filter(is_superuser=True)  # or is_superadmin=True depending on your model
    admin_emails = [admin.email for admin in super_admins if admin.email]

    subject = "Car Booking Confirmation"
    body = f"""
    Hello {user_name},

    Your booking for the car '{car_name}' has been confirmed.
    Booking details:
    Start Time: {start_time}
    End Time: {end_time}

    Thank you for using our service!

    -- Admin Team
    """

    # Create the email message for user
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = user_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Create the email message for admins
    admin_subject = "New Car Booking Notification"
    admin_body = f"""
    Hello Admin,

    A new car booking has been made by {user_name}.

    Car: {car_name}
    Start Time: {start_time}
    End Time: {end_time}

    Please review the booking.

    -- System
    """

    admin_message = MIMEMultipart()
    admin_message["From"] = sender_email
    admin_message["To"] = ", ".join(admin_emails)  # multiple recipients
    admin_message["Subject"] = admin_subject
    admin_message.attach(MIMEText(admin_body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        # Send email to user
        server.sendmail(sender_email, user_email, message.as_string())
        # Send email to all super admins
        server.sendmail(sender_email, admin_emails, admin_message.as_string())
        print("Booking confirmation emails sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        server.quit()