"""
URL patterns for the Dental Clinic core application.
"""

from django.urls import path
from . import views

urlpatterns = [
    # ---- Public Pages ----
    path('', views.home, name='home'),
    path('doctors/', views.doctors_list, name='doctors_list'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),

    # ---- Authentication ----
    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),

    # ---- Appointments ----
    path('book/', views.book_appointment, name='book_appointment'),
    path('booking/success/<str:appointment_id>/', views.appointment_success, name='appointment_success'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('appointment/<str:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<str:appointment_id>/edit/', views.edit_appointment, name='edit_appointment'),
    path('appointment/<str:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),

    # ---- AJAX Endpoints ----
    path('ajax/doctor-schedule/<int:doctor_id>/', views.get_doctor_schedule, name='get_doctor_schedule'),
    path('ajax/available-slots/', views.get_available_slots, name='get_available_slots'),

    # ---- Admin Panel ----
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),

    # Admin - Doctors
    path('admin-panel/doctors/', views.admin_doctors, name='admin_doctors'),
    path('admin-panel/doctors/add/', views.admin_add_doctor, name='admin_add_doctor'),
    path('admin-panel/doctors/<int:pk>/edit/', views.admin_edit_doctor, name='admin_edit_doctor'),
    path('admin-panel/doctors/<int:pk>/delete/', views.admin_delete_doctor, name='admin_delete_doctor'),
    path('admin-panel/doctors/<int:doctor_id>/schedule/add/', views.admin_add_schedule, name='admin_add_schedule'),
    path('admin-panel/schedule/<int:schedule_id>/delete/', views.admin_delete_schedule, name='admin_delete_schedule'),

    # Admin - Appointments
    path('admin-panel/appointments/', views.admin_appointments, name='admin_appointments'),
    path('admin-panel/appointments/<str:appointment_id>/', views.admin_appointment_detail, name='admin_appointment_detail'),

    # Admin - Users
    path('admin-panel/users/', views.admin_users, name='admin_users'),
]
