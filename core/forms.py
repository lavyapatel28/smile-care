"""
Forms for the Dental Clinic Appointment System.

Forms:
    - UserRegistrationForm: New user registration
    - AppointmentForm: Book new appointment
    - AppointmentEditForm: Edit existing appointment
    - DoctorForm: Add/edit doctor (admin)
    - DoctorScheduleForm: Add schedule for a doctor (admin)
    - AppointmentStatusForm: Update appointment status (admin)
    - RescheduleForm: Reschedule appointment (admin)
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Doctor, DoctorSchedule, Appointment
import re


class UserRegistrationForm(UserCreationForm):
    """Form for registering a new user account."""
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'id': 'id_first_name'
        })
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'id': 'id_last_name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'id': 'id_email'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (optional)',
            'id': 'id_phone'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to all fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
            'id': 'id_username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'id_password1'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'id': 'id_password2'
        })
        # Remove verbose help texts
        self.fields['username'].help_text = 'Required. 150 characters or fewer.'
        self.fields['password1'].help_text = 'At least 6 characters.'
        self.fields['password2'].help_text = 'Enter the same password again.'

    def clean_email(self):
        """Ensure email is unique across all users."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove spaces and dashes for validation
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
            if not re.match(r'^\+?[0-9]{7,15}$', cleaned_phone):
                raise forms.ValidationError("Enter a valid phone number.")
        return phone


class AppointmentForm(forms.ModelForm):
    """Form for booking a new dental appointment."""

    GENDER_CHOICES = [
        ('', '-- Select Gender --'),
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    patient_gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_patient_gender'
        })
    )

    class Meta:
        model = Appointment
        fields = [
            'doctor', 'appointment_date', 'appointment_time',
            'patient_name', 'patient_email', 'patient_phone',
            'patient_age', 'patient_gender', 'reason'
        ]
        widgets = {
            'doctor': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_doctor',
                'onchange': 'loadDoctorSchedule(this.value)'
            }),
            'appointment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_appointment_date',
                'onchange': 'loadAvailableSlots()'
            }),
            'appointment_time': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_appointment_time'
            }),
            'patient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name',
                'id': 'id_patient_name'
            }),
            'patient_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address',
                'id': 'id_patient_email'
            }),
            'patient_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number',
                'id': 'id_patient_phone'
            }),
            'patient_age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Age',
                'min': '1',
                'max': '120',
                'id': 'id_patient_age'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe your dental problem or reason for visit...',
                'rows': 4,
                'id': 'id_reason'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show available doctors
        self.fields['doctor'].queryset = Doctor.objects.filter(is_available=True)
        self.fields['doctor'].widget.attrs['class'] = 'form-select'
        self.fields['doctor'].empty_label = '-- Select Doctor --'
        # Time choices will be populated dynamically via AJAX
        self.fields['appointment_time'].widget = forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_appointment_time'
        })
        self.fields['appointment_time'].choices = [('', '-- Select Date First --')]

    def clean_patient_phone(self):
        """Validate patient phone number."""
        phone = self.cleaned_data.get('patient_phone')
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        if not re.match(r'^\+?[0-9]{7,15}$', cleaned_phone):
            raise forms.ValidationError("Enter a valid phone number (7-15 digits).")
        return phone

    def clean_patient_age(self):
        """Validate patient age."""
        age = self.cleaned_data.get('patient_age')
        if age and (age < 1 or age > 120):
            raise forms.ValidationError("Please enter a valid age between 1 and 120.")
        return age

    def clean(self):
        """Check for duplicate booking and slot availability."""
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')

        if doctor and appointment_date and appointment_time:
            # Check for duplicate booking - same doctor, date, and time
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['pending', 'approved', 'rescheduled']
            )
            # Exclude current instance if editing
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                time_formatted = appointment_time.strftime('%I:%M %p') if hasattr(appointment_time, 'strftime') else str(appointment_time)
                date_formatted = appointment_date.strftime('%d-%m-%Y') if hasattr(appointment_date, 'strftime') else str(appointment_date)
                raise forms.ValidationError(
                    f"The {time_formatted} time slot for Dr. {doctor.name} on {date_formatted} is already booked by another patient. Please select a different time slot."
                )

        return cleaned_data


class AppointmentEditForm(forms.ModelForm):
    """Form for editing an existing appointment (patient side)."""

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    patient_gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Appointment
        fields = [
            'doctor', 'appointment_date', 'appointment_time',
            'patient_name', 'patient_email', 'patient_phone',
            'patient_age', 'patient_gender', 'reason'
        ]
        widgets = {
            'doctor': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'loadDoctorSchedule(this.value)'
            }),
            'appointment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'onchange': 'loadAvailableSlots()'
            }),
            'appointment_time': forms.Select(attrs={'class': 'form-select'}),
            'patient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'patient_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '120'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = Doctor.objects.filter(is_available=True)
        self.fields['doctor'].empty_label = '-- Select Doctor --'


class DoctorForm(forms.ModelForm):
    """Form for adding or editing a doctor (admin use)."""

    class Meta:
        model = Doctor
        fields = [
            'name', 'specialization', 'image', 'bio',
            'experience', 'phone', 'email', 'qualification',
            'consultation_fee', 'is_available'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doctor Full Name'}),
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Short biography...'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., BDS, MDS, PhD'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DoctorScheduleForm(forms.ModelForm):
    """Form for setting a doctor's schedule (admin use)."""

    class Meta:
        model = DoctorSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'slot_duration': forms.Select(
                choices=[(15, '15 minutes'), (30, '30 minutes'), (45, '45 minutes'), (60, '60 minutes')],
                attrs={'class': 'form-select'}
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned_data


class AppointmentStatusForm(forms.ModelForm):
    """Form for updating appointment status (admin use)."""

    class Meta:
        model = Appointment
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add notes for the patient...'
            }),
        }


class RescheduleForm(forms.Form):
    """Form for rescheduling an appointment (admin use)."""
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for rescheduling...'
        })
    )
