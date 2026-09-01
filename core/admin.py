"""
Django Admin configuration for the Dental Clinic system.
Registers all models with customized admin interfaces.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Doctor, DoctorSchedule, Appointment, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'gender', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    list_filter = ['gender']


class DoctorScheduleInline(admin.TabularInline):
    """Inline admin for doctor schedules."""
    model = DoctorSchedule
    extra = 1
    fields = ['day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    """Admin for Doctor model with inline schedules."""
    list_display = ['get_name', 'specialization', 'experience', 'phone', 'is_available', 'consultation_fee']
    list_filter = ['specialization', 'is_available']
    search_fields = ['name', 'specialization', 'email']
    inlines = [DoctorScheduleInline]
    list_editable = ['is_available']

    def get_name(self, obj):
        return f"Dr. {obj.name}"
    get_name.short_description = 'Doctor Name'

    def get_photo(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="50" style="border-radius:50%"/>', obj.image.url)
        return '—'
    get_photo.short_description = 'Photo'


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active']
    list_filter = ['day_of_week', 'is_active', 'doctor']
    search_fields = ['doctor__name']
    list_editable = ['is_active']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin for Appointment model with search, filter, and actions."""
    list_display = [
        'appointment_id', 'patient_name', 'doctor', 'appointment_date',
        'appointment_time', 'get_status_colored', 'created_at'
    ]
    list_filter = ['status', 'doctor', 'appointment_date']
    search_fields = [
        'appointment_id', 'patient_name', 'patient_email',
        'patient_phone', 'doctor__name'
    ]
    readonly_fields = ['appointment_id', 'created_at', 'updated_at']
    list_per_page = 25
    date_hierarchy = 'appointment_date'

    fieldsets = (
        ('Appointment Info', {
            'fields': ('appointment_id', 'doctor', 'appointment_date', 'appointment_time', 'status')
        }),
        ('Patient Info', {
            'fields': ('patient_name', 'patient_email', 'patient_phone', 'patient_age', 'patient_gender')
        }),
        ('Details', {
            'fields': ('reason', 'admin_notes')
        }),
        ('System Info', {
            'fields': ('user', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_status_colored(self, obj):
        """Display status with color badge."""
        colors = {
            'pending': '#FFC107',
            'approved': '#28A745',
            'rejected': '#DC3545',
            'cancelled': '#6C757D',
            'completed': '#17A2B8',
            'rescheduled': '#007BFF',
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:4px;font-size:12px">{}</span>',
            color, obj.get_status_display()
        )
    get_status_colored.short_description = 'Status'

    actions = ['approve_appointments', 'reject_appointments', 'mark_completed']

    def approve_appointments(self, request, queryset):
        queryset.filter(status='pending').update(status='approved')
        self.message_user(request, "Selected appointments have been approved.")
    approve_appointments.short_description = "Approve selected appointments"

    def reject_appointments(self, request, queryset):
        queryset.filter(status__in=['pending', 'approved']).update(status='rejected')
        self.message_user(request, "Selected appointments have been rejected.")
    reject_appointments.short_description = "Reject selected appointments"

    def mark_completed(self, request, queryset):
        queryset.filter(status='approved').update(status='completed')
        self.message_user(request, "Selected appointments marked as completed.")
    mark_completed.short_description = "Mark selected as completed"


# Customize admin site header
admin.site.site_header = "SmileCare Dental Admin"
admin.site.site_title = "Dental Admin"
admin.site.index_title = "Hospital Management"
