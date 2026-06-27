# ZPPS School Student Portal

A full-featured school management portal for Zilla Parishad Primary School (ZPPS).

## Features

| Module | Admin | Teacher | Student | Parent |
|--------|-------|---------|---------|--------|
| Dashboard | ✅ Stats | ✅ Quick actions | ✅ Progress | ✅ Child info |
| Student Mgmt | ✅ CRUD | - | ✅ Profile | ✅ View |
| Teacher Mgmt | ✅ CRUD | - | - | - |
| Classes & Subjects | ✅ CRUD | - | - | - |
| Attendance | ✅ View All | ✅ Mark + View | ✅ View | ✅ View |
| Marks | ✅ View All | ✅ Enter | ✅ View | ✅ View |
| Timetable | ✅ Manage | ✅ View | ✅ View | ✅ View |
| Fee Management | ✅ CRUD | - | ✅ View | ✅ View |
| Notice Board | ✅ CRUD | ✅ Post | ✅ View | ✅ View |
| Library | ✅ Manage | - | ✅ View/Borrow | - |
| Homework | ✅ View | ✅ Assign | ✅ View | ✅ View |
| Class Tests (MCQ) | ✅ View | ✅ Create | ✅ Take | - |

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. MySQL Setup
Create database:
```sql
CREATE DATABASE zpps_school_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

In `zpps_portal/settings.py`, comment out SQLite and uncomment MySQL config:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zpps_school_db',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 3. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 5. Run Server
```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000/

## Demo Credentials (for testing)
| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Teacher | EMP001 | teacher123 |
| Student | STU001 | student123 |
| Parent | PAR001 | parent123 |

## Project Structure
```
zpps_portal/
├── portal/
│   ├── models.py       # All database models
│   ├── views.py        # All views/logic
│   ├── forms.py        # All forms
│   ├── urls.py         # URL routing
│   ├── admin.py        # Admin panel config
│   └── templatetags/   # Custom template tags
├── templates/
│   └── portal/
│       ├── base.html   # Base template
│       ├── login.html  # Login page
│       ├── dashboard.html
│       ├── admin/      # Admin templates
│       ├── teacher/    # Teacher templates
│       └── student/    # Student templates
├── static/             # CSS, JS files
└── requirements.txt
```

## Tech Stack
- **Backend**: Python 3, Django 4.2
- **Database**: MySQL (SQLite for dev)
- **Frontend**: Bootstrap 5.3, Bootstrap Icons
- **Other**: Pillow (image uploads)
