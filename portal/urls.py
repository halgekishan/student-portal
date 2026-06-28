from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Admin - Students
    path('students/', views.manage_students, name='manage_students'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:pk>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:pk>/delete/', views.delete_student, name='delete_student'),

    # Admin - Teachers
    path('teachers/', views.manage_teachers, name='manage_teachers'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/<int:pk>/edit/', views.edit_teacher, name='edit_teacher'),
    path('teachers/<int:pk>/delete/', views.delete_teacher, name='delete_teacher'),

    # Admin - Classes
    path('classes/', views.manage_classes, name='manage_classes'),
    path('classes/add/', views.add_class, name='add_class'),
    path('classes/<int:pk>/edit/', views.edit_class, name='edit_class'),

    # Admin - Subjects
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('subjects/add/', views.add_subject, name='add_subject'),

    # Attendance
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/', views.view_attendance, name='view_attendance'),

    # Marks
    path('marks/enter/', views.enter_marks, name='enter_marks'),
    path('marks/', views.view_marks, name='view_marks'),

    # Timetable
    path('timetable/', views.view_timetable, name='view_timetable'),

    # Fees
    path('fees/', views.manage_fees, name='manage_fees'),
    path('fees/add/', views.add_fee, name='add_fee'),

    # Notices
    path('notices/', views.notice_board, name='notice_board'),
    path('notices/add/', views.add_notice, name='add_notice'),
    path('notices/<int:pk>/delete/', views.delete_notice, name='delete_notice'),

    # Library
    path('library/', views.library, name='library'),
    path('library/add-book/', views.add_book, name='add_book'),
    path('library/issue/<int:book_id>/', views.issue_book, name='issue_book'),
    path('library/return/<int:issue_id>/', views.return_book, name='return_book'),

    # Homework
    path('homework/', views.homework, name='homework'),
    path('homework/add/', views.add_homework, name='add_homework'),

    # Tests
    path('tests/', views.class_tests, name='class_tests'),
    path('tests/create/', views.create_test, name='create_test'),
    path('tests/<int:test_id>/questions/', views.add_questions, name='add_questions'),
    path('tests/<int:test_id>/take/', views.take_test, name='take_test'),
    path('tests/result/<int:attempt_id>/', views.test_result, name='test_result'),

    # Profile
    path('profile/', views.student_profile, name='student_profile'),


    # Parent Management
    path('parents/', views.manage_parents, name='manage_parents'),
    path('parents/add/', views.add_parent, name='add_parent'),
    path('parents/<int:pk>/edit/', views.edit_parent, name='edit_parent'),
    path('parents/<int:pk>/delete/', views.delete_parent, name='delete_parent'),

    # Progress Reports
    path('report/my/', views.progress_report, name='progress_report'),
    path('report/student/<int:student_id>/', views.progress_report, name='student_progress'),
    path('report/all/', views.all_students_progress, name='all_progress'),
]
