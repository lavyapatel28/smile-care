# SmileCare Dental Hospital - Online Appointment Booking System

A complete, production-ready Online Dental Appointment Booking System built with Django, Bootstrap 5, and SQLite.

## Features

### Public Website
- Modern dental clinic landing page
- Hero section with animations
- Services section
- Doctor profiles with working schedule
- Contact information with Google Maps
- Responsive design (Desktop, Tablet, Mobile)

### User Features
- User Registration & Login
- Book Appointment (Select Doctor → Date → Time Slot → Patient Details)
- View Upcoming Appointments
- View Appointment History
- Edit Pending Appointments
- Cancel Pending Appointments

### Admin Panel
- Dashboard with statistics (total appointments, today's, doctors, patients)
- Manage Doctors (Add / Edit / Delete)
- Set Doctor Schedules (Day, Start Time, End Time, Slot Duration)
- Manage Appointments (View All / Search / Filter)
- Approve / Reject / Cancel / Reschedule appointments
- View all registered patients

### Technical Features
- Auto-generated Appointment IDs (DA-YYYYMMDD-XXXXX)
- AJAX-based available slot fetching
- Double-booking prevention
- CSRF Protection
- Email & Phone validation
- Working day restrictions in date picker

## Project Structure

```
dental_clinic/
├── manage.py
├── requirements.txt
├── dental_clinic/         # Django settings & config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                  # Main app
│   ├── models.py          # Doctor, DoctorSchedule, Appointment, UserProfile
│   ├── views.py           # All views
│   ├── urls.py            # URL patterns
│   ├── forms.py           # Django forms
│   └── admin.py           # Django admin config
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── auth/
│   ├── appointments/
│   ├── doctors/
│   └── admin_panel/
└── static/
    ├── css/style.css
    └── js/main.js
```

## Installation & Setup

### 1. Navigate to project directory
```bash
cd "dental_clinic"
```

### 2. Create & activate virtual environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create superuser (Admin)
```bash
python manage.py createsuperuser
```

### 6. Run development server
```bash
python manage.py runserver
```

### 7. Open browser
- **Website**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin-panel/
- **Django Admin**: http://127.0.0.1:8000/django-admin/

## Getting Started

1. Login to the Admin Panel at `/admin-panel/`
2. Add Doctors with their specialization
3. Set working schedules for each doctor (day, start/end time, slot duration)
4. Register as a patient and book appointments!

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Django 4.2 |
| Frontend | HTML5, CSS3, Bootstrap 5.3, JavaScript |
| Database | SQLite |
| Icons | Bootstrap Icons |
| Fonts | Google Fonts (Inter, Outfit) |

## Colors

- **Primary**: `#0EA5E9` (Sky Blue)
- **Dark**: `#0F172A` (Slate Dark)
- **Accent**: `#6366F1` (Indigo)

## License

MIT License - SmileCare Dental Hospital System
