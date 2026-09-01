"""
Core application models for Dental Clinic Appointment System.

Models:
    - Doctor: Dental doctors with their specializations and availability
    - DoctorSchedule: Weekly schedule with time slots for each doctor
    - Appointment: Patient appointment bookings
    - UserProfile: Extended user information
"""

from django.db import models
from django.contrib.auth.models import User
import random
import string
from datetime import datetime, timedelta


# Specialization choices for doctors
SPECIALIZATION_CHOICES = [
    ('General Dentist', 'General Dentist'),
    ('Orthodontist', 'Orthodontist'),
    ('Periodontist', 'Periodontist'),
    ('Endodontist', 'Endodontist'),
    ('Oral Surgeon', 'Oral Surgeon'),
    ('Pediatric Dentist', 'Pediatric Dentist'),
    ('Prosthodontist', 'Prosthodontist'),
    ('Cosmetic Dentist', 'Cosmetic Dentist'),
]

# Days of the week for scheduling
DAYS_OF_WEEK = [
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
]

# Day number mapping for Python's weekday() function (0=Monday, 6=Sunday)
DAY_NUMBER_MAP = {
    'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
    'Friday': 4, 'Saturday': 5, 'Sunday': 6
}


class UserProfile(models.Model):
    """Extended profile for registered users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')
    ], blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} Profile"


class Doctor(models.Model):
    """Model representing a dental doctor."""
    name = models.CharField(max_length=200, help_text="Full name of the doctor (without Dr.)")
    specialization = models.CharField(
        max_length=100,
        choices=SPECIALIZATION_CHOICES,
        default='General Dentist'
    )
    image = models.ImageField(
        upload_to='doctors/',
        null=True,
        blank=True,
        help_text="Doctor's profile photo"
    )
    bio = models.TextField(blank=True, help_text="Short biography of the doctor")
    experience = models.IntegerField(default=0, help_text="Years of experience")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    qualification = models.CharField(max_length=300, blank=True, help_text="e.g., BDS, MDS, PhD")
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    is_available = models.BooleanField(default=True, help_text="Is the doctor currently available?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"Dr. {self.name} - {self.specialization}"

    def get_working_days(self):
        """Returns list of working day names from schedules."""
        return list(self.schedules.filter(is_active=True).values_list('day_of_week', flat=True))

    def get_working_day_numbers(self):
        """Returns list of weekday numbers (0=Mon, 6=Sun) for JS date picker."""
        days = self.get_working_days()
        return [DAY_NUMBER_MAP[d] for d in days if d in DAY_NUMBER_MAP]


class DoctorSchedule(models.Model):
    """Weekly schedule and time slots for a doctor."""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=20, choices=DAYS_OF_WEEK)
    start_time = models.TimeField(help_text="Clinic start time (e.g., 09:00)")
    end_time = models.TimeField(help_text="Clinic end time (e.g., 17:00)")
    slot_duration = models.IntegerField(
        default=30,
        help_text="Duration of each appointment slot in minutes"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week']

    def __str__(self):
        return f"Dr. {self.doctor.name} - {self.day_of_week} ({self.start_time} - {self.end_time})"

    def generate_time_slots(self):
        """Generate all time slots for this schedule."""
        slots = []
        current = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        delta = timedelta(minutes=self.slot_duration)

        while current + delta <= end:
            slots.append(current.time())
            current += delta

        return slots


class Appointment(models.Model):
    """Model representing a patient's dental appointment."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('rescheduled', 'Rescheduled'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    # Auto-generated unique appointment ID
    appointment_id = models.CharField(max_length=25, unique=True, editable=False)

    # Linked user (optional - can book without account)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments'
    )

    # Doctor assigned
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    # Patient information
    patient_name = models.CharField(max_length=200)
    patient_email = models.EmailField()
    patient_phone = models.CharField(max_length=20)
    patient_age = models.PositiveIntegerField()
    patient_gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    # Appointment details
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField(help_text="Reason or problem description")

    # Status and admin notes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Notes from admin/doctor")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.appointment_id} - {self.patient_name} with Dr. {self.doctor.name}"

    def save(self, *args, **kwargs):
        """Generate unique appointment ID before saving."""
        if not self.appointment_id:
            self.appointment_id = self._generate_appointment_id()
        super().save(*args, **kwargs)

    def _generate_appointment_id(self):
        """Generate a unique appointment ID in format DA-YYYYMMDD-XXXXX."""
        from datetime import date
        date_str = date.today().strftime('%Y%m%d')
        while True:
            random_str = ''.join(random.choices(string.digits, k=5))
            apt_id = f'DA-{date_str}-{random_str}'
            if not Appointment.objects.filter(appointment_id=apt_id).exists():
                return apt_id

    def get_status_badge_class(self):
        """Return Bootstrap badge class based on status."""
        status_classes = {
            'pending': 'bg-warning text-dark',
            'approved': 'bg-success',
            'rejected': 'bg-danger',
            'cancelled': 'bg-secondary',
            'completed': 'bg-info',
            'rescheduled': 'bg-primary',
        }
        return status_classes.get(self.status, 'bg-secondary')

    def can_cancel(self):
        """Check if appointment can be cancelled (only pending appointments)."""
        return self.status == 'pending'

    def can_edit(self):
        """Check if appointment can be edited (only pending appointments)."""
        return self.status == 'pending'
