"""
Views for the Dental Clinic Appointment System.

Organized into sections:
    1. Public Views (Home, Doctors)
    2. Authentication Views (Register, Login, Logout)
    3. Appointment Views (Book, Dashboard, Detail, Edit, Cancel)
    4. Admin Panel Views (Dashboard, Doctors, Appointments, Users)
    5. AJAX Views (Get available slots)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Doctor, DoctorSchedule, Appointment, UserProfile, DAY_NUMBER_MAP
from .forms import (
    UserRegistrationForm, AppointmentForm, AppointmentEditForm,
    DoctorForm, DoctorScheduleForm, AppointmentStatusForm, RescheduleForm
)

from datetime import datetime, date, timedelta
import json


# ============================================================
# Helper Functions
# ============================================================

def is_admin(user):
    """Check if user is staff/admin."""
    return user.is_authenticated and user.is_staff


def get_all_time_slots_with_status(doctor, appointment_date):
    """
    Returns list of dicts for time slots for a doctor on a given date:
    [{'slot': datetime.time(9, 0), 'is_booked': False}, ...]
    Includes default schedule (Mon-Sat 09:00 - 17:00, 30-min duration) if no custom schedule is defined.
    """
    day_name = appointment_date.strftime('%A')

    # Get doctor's schedule for this day
    schedules = DoctorSchedule.objects.filter(
        doctor=doctor,
        day_of_week=day_name,
        is_active=True
    )

    all_slots = []
    if schedules.exists():
        for schedule in schedules:
            all_slots.extend(schedule.generate_time_slots())
    else:
        # Default schedule if no custom DoctorSchedule exists: Mon-Sat 09:00 to 17:00 (30 min slots)
        if day_name != 'Sunday':
            current = datetime.combine(datetime.today(), datetime.strptime("09:00", "%H:%M").time())
            end = datetime.combine(datetime.today(), datetime.strptime("17:00", "%H:%M").time())
            delta = timedelta(minutes=30)
            while current + delta <= end:
                all_slots.append(current.time())
                current += delta

    # Fetch booked slots (pending, approved, rescheduled)
    booked_slots = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        status__in=['pending', 'approved', 'rescheduled']
    ).values_list('appointment_time', flat=True)

    booked_times = set(t for t in booked_slots)

    result = []
    for slot in all_slots:
        result.append({
            'slot': slot,
            'is_booked': (slot in booked_times)
        })

    return result


def get_available_time_slots(doctor, appointment_date):
    """
    Returns list of unbooked time slots for a doctor on a given date.
    """
    slots_info = get_all_time_slots_with_status(doctor, appointment_date)
    return [item['slot'] for item in slots_info if not item['is_booked']]


# ============================================================
# 1. Public Views
# ============================================================

def home(request):
    """Main landing page with hero, services, doctors, and contact sections."""
    doctors = Doctor.objects.filter(is_available=True)[:6]
    context = {
        'doctors': doctors,
        'page_title': 'SmileCare Dental Hospital - Expert Dental Care',
    }
    return render(request, 'home.html', context)


def doctors_list(request):
    """List all available doctors."""
    doctors = Doctor.objects.filter(is_available=True)
    context = {
        'doctors': doctors,
        'page_title': 'Our Doctors - SmileCare Dental',
    }
    return render(request, 'doctors/list.html', context)


def doctor_detail(request, pk):
    """Detail page for a single doctor."""
    doctor = get_object_or_404(Doctor, pk=pk, is_available=True)
    schedules = doctor.schedules.filter(is_active=True).order_by('day_of_week')
    context = {
        'doctor': doctor,
        'schedules': schedules,
        'page_title': f'Dr. {doctor.name} - SmileCare Dental',
    }
    return render(request, 'doctors/detail.html', context)


# ============================================================
# 2. Authentication Views
# ============================================================

def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('book_appointment')

    next_url = request.GET.get('next') or request.POST.get('next', '')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            # Create user profile
            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone', '')
            )

            # Auto-login after registration
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Account created successfully.')
            if next_url:
                return redirect(next_url)
            return redirect('book_appointment')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()

    return render(request, 'auth/register.html', {
        'form': form,
        'next': next_url,
        'page_title': 'Register - SmileCare Dental',
    })


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'auth/login.html', {'page_title': 'Login - SmileCare Dental'})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next') or request.POST.get('next', '')
            if user.is_staff:
                if next_url and next_url != 'dashboard':
                    return redirect(next_url)
                return redirect('admin_dashboard')
            else:
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'auth/login.html', {'page_title': 'Login - SmileCare Dental'})


def logout_view(request):
    """Logout and redirect to home."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


# ============================================================
# 3. Appointment Views
# ============================================================

@login_required
def book_appointment(request):
    """Book a new dental appointment."""
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            # Pre-fill patient info from user if empty
            if not appointment.patient_name:
                appointment.patient_name = request.user.get_full_name()
            if not appointment.patient_email:
                appointment.patient_email = request.user.email
            appointment.save()
            messages.success(request, f'Appointment booked successfully! Your ID: {appointment.appointment_id}')
            return redirect('appointment_success', appointment_id=appointment.appointment_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill user info
        user = request.user
        initial_data = {
            'patient_name': user.get_full_name(),
            'patient_email': user.email,
        }
        try:
            profile = user.profile
            initial_data['patient_phone'] = profile.phone
        except UserProfile.DoesNotExist:
            pass
        form = AppointmentForm(initial=initial_data)

    doctors = Doctor.objects.filter(is_available=True)
    return render(request, 'appointments/book.html', {
        'form': form,
        'doctors': doctors,
        'page_title': 'Book Appointment - SmileCare Dental',
    })


def appointment_success(request, appointment_id):
    """Success page after booking an appointment."""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)
    return render(request, 'appointments/success.html', {
        'appointment': appointment,
        'page_title': 'Appointment Confirmed - SmileCare Dental',
    })


@login_required
def user_dashboard(request):
    """User's personal dashboard showing their appointments."""
    appointments = Appointment.objects.filter(user=request.user).order_by('-created_at')

    # Separate upcoming and past
    today = date.today()
    upcoming = appointments.filter(
        appointment_date__gte=today,
        status__in=['pending', 'approved', 'rescheduled']
    )
    history = appointments.filter(
        Q(appointment_date__lt=today) | Q(status__in=['cancelled', 'rejected', 'completed'])
    )

    context = {
        'appointments': appointments,
        'upcoming': upcoming,
        'history': history,
        'page_title': 'My Appointments - SmileCare Dental',
    }
    return render(request, 'appointments/dashboard.html', context)


@login_required
def appointment_detail(request, appointment_id):
    """View details of a specific appointment."""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, user=request.user)
    return render(request, 'appointments/detail.html', {
        'appointment': appointment,
        'page_title': f'Appointment {appointment_id} - SmileCare Dental',
    })


@login_required
def edit_appointment(request, appointment_id):
    """Edit a pending appointment."""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, user=request.user)

    if not appointment.can_edit():
        messages.error(request, 'Only pending appointments can be edited.')
        return redirect('appointment_detail', appointment_id=appointment_id)

    if request.method == 'POST':
        form = AppointmentEditForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Appointment updated successfully!')
            return redirect('appointment_detail', appointment_id=appointment_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentEditForm(instance=appointment)

    return render(request, 'appointments/edit.html', {
        'form': form,
        'appointment': appointment,
        'page_title': f'Edit Appointment - SmileCare Dental',
    })


@login_required
def cancel_appointment(request, appointment_id):
    """Cancel a pending appointment."""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id, user=request.user)

    if not appointment.can_cancel():
        messages.error(request, 'Only pending appointments can be cancelled.')
        return redirect('dashboard')

    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, f'Appointment {appointment_id} has been cancelled.')
        return redirect('dashboard')

    return render(request, 'appointments/cancel_confirm.html', {
        'appointment': appointment,
        'page_title': 'Cancel Appointment - SmileCare Dental',
    })


# ============================================================
# 4. AJAX Views
# ============================================================

@require_GET
def get_doctor_schedule(request, doctor_id):
    """
    AJAX endpoint: Returns doctor's working days and slot info.
    Used to disable non-working days in date picker.
    """
    try:
        doctor = Doctor.objects.get(pk=doctor_id, is_available=True)
        schedules = DoctorSchedule.objects.filter(doctor=doctor, is_active=True)

        working_days = []
        for schedule in schedules:
            day_num = DAY_NUMBER_MAP.get(schedule.day_of_week, -1)
            if day_num >= 0 and day_num not in working_days:
                working_days.append(day_num)

        # Default working days if no custom schedules defined: Monday to Saturday (0, 1, 2, 3, 4, 5)
        if not working_days:
            working_days = [0, 1, 2, 3, 4, 5]

        return JsonResponse({
            'success': True,
            'working_days': working_days,  # 0=Mon, 6=Sun
            'doctor_name': f'Dr. {doctor.name}',
        })
    except Doctor.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Doctor not found'}, status=404)


@require_GET
def get_available_slots(request):
    """
    AJAX endpoint: Returns time slots for a doctor on a specific date with booked status.
    """
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'success': False, 'message': 'Missing parameters'}, status=400)

    try:
        doctor = Doctor.objects.get(pk=doctor_id, is_available=True)
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Prevent booking past dates
        if appointment_date < date.today():
            return JsonResponse({'success': False, 'message': 'Cannot book past dates'}, status=400)

        slots_info = get_all_time_slots_with_status(doctor, appointment_date)

        slots_data = [
            {
                'value': item['slot'].strftime('%H:%M:%S'),
                'display': item['slot'].strftime('%I:%M %p'),
                'is_booked': item['is_booked']
            }
            for item in slots_info
        ]

        free_count = sum(1 for item in slots_info if not item['is_booked'])

        return JsonResponse({
            'success': True,
            'slots': slots_data,
            'count': free_count,
            'total_slots': len(slots_data),
        })
    except Doctor.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Doctor not found'}, status=404)
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid date format'}, status=400)


# ============================================================
# 5. Admin Panel Views
# ============================================================

def admin_required(view_func):
    """Decorator to restrict view to admin/staff users."""
    decorated_view = user_passes_test(
        is_admin,
        login_url='/auth/login/'
    )(view_func)
    return decorated_view


@admin_required
def admin_dashboard(request):
    """Admin dashboard with statistics overview."""
    today = date.today()

    # Statistics
    total_appointments = Appointment.objects.count()
    today_appointments = Appointment.objects.filter(appointment_date=today).count()
    total_doctors = Doctor.objects.count()
    total_patients = User.objects.filter(is_staff=False).count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    approved_appointments = Appointment.objects.filter(status='approved').count()

    # Recent appointments
    recent_appointments = Appointment.objects.select_related('doctor', 'user').order_by('-created_at')[:10]

    # Upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        appointment_date__gte=today,
        status__in=['pending', 'approved']
    ).select_related('doctor').order_by('appointment_date', 'appointment_time')[:10]

    context = {
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'pending_appointments': pending_appointments,
        'approved_appointments': approved_appointments,
        'recent_appointments': recent_appointments,
        'upcoming_appointments': upcoming_appointments,
        'page_title': 'Admin Dashboard - SmileCare Dental',
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_doctors(request):
    """List all doctors."""
    search_query = request.GET.get('search', '')
    doctors = Doctor.objects.all()
    if search_query:
        doctors = doctors.filter(
            Q(name__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )
    context = {
        'doctors': doctors,
        'search_query': search_query,
        'page_title': 'Manage Doctors - Admin',
    }
    return render(request, 'admin_panel/doctors/list.html', context)


@admin_required
def admin_add_doctor(request):
    """Add a new doctor."""
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save()
            messages.success(request, f'Dr. {doctor.name} has been added successfully!')
            return redirect('admin_doctors')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorForm()

    return render(request, 'admin_panel/doctors/add.html', {
        'form': form,
        'page_title': 'Add Doctor - Admin',
    })


@admin_required
def admin_edit_doctor(request, pk):
    """Edit an existing doctor."""
    doctor = get_object_or_404(Doctor, pk=pk)

    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Dr. {doctor.name} updated successfully!')
            return redirect('admin_doctors')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DoctorForm(instance=doctor)

    # Doctor's schedules
    schedules = doctor.schedules.all().order_by('day_of_week')
    schedule_form = DoctorScheduleForm()

    return render(request, 'admin_panel/doctors/edit.html', {
        'form': form,
        'doctor': doctor,
        'schedules': schedules,
        'schedule_form': schedule_form,
        'page_title': f'Edit Dr. {doctor.name} - Admin',
    })


@admin_required
def admin_delete_doctor(request, pk):
    """Delete a doctor."""
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == 'POST':
        name = doctor.name
        doctor.delete()
        messages.success(request, f'Dr. {name} has been deleted.')
        return redirect('admin_doctors')
    return render(request, 'admin_panel/doctors/delete_confirm.html', {
        'doctor': doctor,
        'page_title': f'Delete Dr. {doctor.name} - Admin',
    })


@admin_required
def admin_add_schedule(request, doctor_id):
    """Add a schedule slot for a doctor."""
    doctor = get_object_or_404(Doctor, pk=doctor_id)
    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor
            try:
                schedule.save()
                messages.success(request, f'Schedule added for Dr. {doctor.name} on {schedule.day_of_week}.')
            except Exception:
                messages.error(request, 'Schedule for this day already exists. Please edit existing schedule.')
        else:
            messages.error(request, 'Invalid schedule data.')
    return redirect('admin_edit_doctor', pk=doctor_id)


@admin_required
def admin_delete_schedule(request, schedule_id):
    """Delete a doctor's schedule."""
    schedule = get_object_or_404(DoctorSchedule, pk=schedule_id)
    doctor_id = schedule.doctor.pk
    schedule.delete()
    messages.success(request, 'Schedule removed successfully.')
    return redirect('admin_edit_doctor', pk=doctor_id)


@admin_required
def admin_appointments(request):
    """List and search all appointments."""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    appointments = Appointment.objects.select_related('doctor', 'user').order_by('-created_at')

    if search_query:
        appointments = appointments.filter(
            Q(appointment_id__icontains=search_query) |
            Q(patient_name__icontains=search_query) |
            Q(patient_email__icontains=search_query) |
            Q(patient_phone__icontains=search_query) |
            Q(doctor__name__icontains=search_query)
        )

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date=filter_date)
        except ValueError:
            pass

    context = {
        'appointments': appointments,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': Appointment.STATUS_CHOICES,
        'page_title': 'Manage Appointments - Admin',
    }
    return render(request, 'admin_panel/appointments/list.html', context)


@admin_required
def admin_appointment_detail(request, appointment_id):
    """View and manage a specific appointment (admin)."""
    appointment = get_object_or_404(Appointment, appointment_id=appointment_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')

        if action == 'approve':
            appointment.status = 'approved'
            appointment.admin_notes = admin_notes
            appointment.save()
            messages.success(request, f'Appointment {appointment_id} approved.')
        elif action == 'reject':
            appointment.status = 'rejected'
            appointment.admin_notes = admin_notes
            appointment.save()
            messages.warning(request, f'Appointment {appointment_id} rejected.')
        elif action == 'cancel':
            appointment.status = 'cancelled'
            appointment.admin_notes = admin_notes
            appointment.save()
            messages.info(request, f'Appointment {appointment_id} cancelled.')
        elif action == 'complete':
            appointment.status = 'completed'
            appointment.admin_notes = admin_notes
            appointment.save()
            messages.success(request, f'Appointment {appointment_id} marked as completed.')
        elif action == 'reschedule':
            new_date = request.POST.get('new_date')
            new_time = request.POST.get('new_time')
            if new_date and new_time:
                try:
                    appointment.appointment_date = datetime.strptime(new_date, '%Y-%m-%d').date()
                    appointment.appointment_time = datetime.strptime(new_time, '%H:%M').time()
                    appointment.status = 'rescheduled'
                    appointment.admin_notes = admin_notes
                    appointment.save()
                    messages.success(request, f'Appointment {appointment_id} rescheduled.')
                except ValueError:
                    messages.error(request, 'Invalid date or time format.')
            else:
                messages.error(request, 'Please provide new date and time for rescheduling.')

        return redirect('admin_appointment_detail', appointment_id=appointment_id)

    return render(request, 'admin_panel/appointments/detail.html', {
        'appointment': appointment,
        'page_title': f'Appointment {appointment_id} - Admin',
    })


@admin_required
def admin_users(request):
    """List all registered users."""
    search_query = request.GET.get('search', '')
    users = User.objects.filter(is_staff=False).order_by('-date_joined')

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Annotate with appointment count
    users = users.annotate(appointment_count=Count('appointments'))

    context = {
        'users': users,
        'search_query': search_query,
        'page_title': 'Manage Users - Admin',
    }
    return render(request, 'admin_panel/users/list.html', context)
