from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Avg, Count, Q

from .models import *
from .forms import *


def get_user_role(user):
    if user.is_superuser or hasattr(user, 'groups') and user.groups.filter(name='Admin').exists():
        if user.is_superuser:
            return 'admin'
    try:
        user.teacher
        return 'teacher'
    except Teacher.DoesNotExist:
        pass
    try:
        user.student
        return 'student'
    except Student.DoesNotExist:
        pass
    try:
        user.parent
        return 'parent'
    except Parent.DoesNotExist:
        pass
    if user.is_superuser:
        return 'admin'
    return 'unknown'


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password!')
    return render(request, 'portal/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    role = get_user_role(request.user)
    context = {'role': role}

    if role == 'admin':
        context.update({
            'total_students': Student.objects.count(),
            'total_teachers': Teacher.objects.count(),
            'total_classes': Class.objects.count(),
            'recent_notices': Notice.objects.filter(is_active=True)[:5],
            'unpaid_fees': Fee.objects.filter(status='U').count(),
        })
    elif role == 'teacher':
        teacher = request.user.teacher
        context.update({
            'teacher': teacher,
            'my_classes': teacher.classes.all(),
            'recent_notices': Notice.objects.filter(is_active=True, audience__in=['ALL', 'TCH'])[:5],
            'pending_homeworks': Homework.objects.filter(assigned_by=teacher).count(),
        })
    elif role == 'student':
        student = request.user.student
        today = timezone.now().date()
        total_days = Attendance.objects.filter(student=student).count()
        present_days = Attendance.objects.filter(student=student, status='P').count()
        attendance_pct = round((present_days / total_days * 100), 1) if total_days > 0 else 0
        context.update({
            'student': student,
            'attendance_pct': attendance_pct,
            'recent_marks': Mark.objects.filter(student=student).order_by('-entered_on')[:5],
            'recent_notices': Notice.objects.filter(is_active=True, audience__in=['ALL', 'STU'])[:5],
            'pending_homeworks': Homework.objects.filter(
                student_class=student.student_class, due_date__gte=today).count(),
            'active_tests': ClassTest.objects.filter(
                student_class=student.student_class, is_active=True).exclude(
                testattempt__student=student).count(),
            'fee_dues': Fee.objects.filter(student=student, status='U').count(),
        })
    elif role == 'parent':
        parent = request.user.parent
        student = parent.student
        today = timezone.now().date()
        total_days = Attendance.objects.filter(student=student).count()
        present_days = Attendance.objects.filter(student=student, status='P').count()
        attendance_pct = round((present_days / total_days * 100), 1) if total_days > 0 else 0
        context.update({
            'parent': parent,
            'student': student,
            'attendance_pct': attendance_pct,
            'recent_marks': Mark.objects.filter(student=student).order_by('-entered_on')[:5],
            'recent_notices': Notice.objects.filter(is_active=True, audience__in=['ALL', 'PAR'])[:5],
            'fee_dues': Fee.objects.filter(student=student, status='U'),
        })
    return render(request, 'portal/dashboard.html', context)


# ================== ADMIN VIEWS ==================

@login_required
def manage_students(request):
    students = Student.objects.select_related('user', 'student_class').all()
    return render(request, 'portal/admin/students.html', {'students': students})


@login_required
def add_student(request):
    form = StudentForm()
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['roll_number'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data.get('email', ''),
                password=form.cleaned_data.get('password') or form.cleaned_data['roll_number']
            )
            student = form.save(commit=False)
            student.user = user
            student.save()
            messages.success(request, f'Student {user.get_full_name()} added successfully!')
            return redirect('manage_students')
    return render(request, 'portal/admin/student_form.html', {'form': form, 'title': 'Add Student'})


@login_required
def edit_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    initial = {
        'first_name': student.user.first_name,
        'last_name': student.user.last_name,
        'email': student.user.email,
    }
    form = StudentForm(instance=student, initial=initial)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student.user.first_name = form.cleaned_data['first_name']
            student.user.last_name = form.cleaned_data['last_name']
            student.user.email = form.cleaned_data.get('email', '')
            if form.cleaned_data.get('password'):
                student.user.set_password(form.cleaned_data['password'])
            student.user.save()
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('manage_students')
    return render(request, 'portal/admin/student_form.html', {'form': form, 'title': 'Edit Student', 'student': student})


@login_required
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.user.delete()
        messages.success(request, 'Student deleted!')
        return redirect('manage_students')
    return render(request, 'portal/confirm_delete.html', {'obj': student, 'type': 'Student'})


@login_required
def manage_teachers(request):
    teachers = Teacher.objects.select_related('user').all()
    return render(request, 'portal/admin/teachers.html', {'teachers': teachers})


@login_required
def add_teacher(request):
    form = TeacherForm()
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['employee_id'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data.get('email', ''),
                password=form.cleaned_data.get('password') or form.cleaned_data['employee_id']
            )
            teacher = form.save(commit=False)
            teacher.user = user
            teacher.save()
            form.save_m2m()
            messages.success(request, f'Teacher {user.get_full_name()} added!')
            return redirect('manage_teachers')
    return render(request, 'portal/admin/teacher_form.html', {'form': form, 'title': 'Add Teacher'})


@login_required
def edit_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    initial = {'first_name': teacher.user.first_name, 'last_name': teacher.user.last_name, 'email': teacher.user.email}
    form = TeacherForm(instance=teacher, initial=initial)
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            teacher.user.first_name = form.cleaned_data['first_name']
            teacher.user.last_name = form.cleaned_data['last_name']
            teacher.user.email = form.cleaned_data.get('email', '')
            if form.cleaned_data.get('password'):
                teacher.user.set_password(form.cleaned_data['password'])
            teacher.user.save()
            form.save()
            messages.success(request, 'Teacher updated!')
            return redirect('manage_teachers')
    return render(request, 'portal/admin/teacher_form.html', {'form': form, 'title': 'Edit Teacher', 'teacher': teacher})


@login_required
def delete_teacher(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        teacher.user.delete()
        messages.success(request, 'Teacher deleted!')
        return redirect('manage_teachers')
    return render(request, 'portal/confirm_delete.html', {'obj': teacher, 'type': 'Teacher'})


@login_required
def manage_classes(request):
    classes = Class.objects.all()
    return render(request, 'portal/admin/classes.html', {'classes': classes})


@login_required
def add_class(request):
    form = ClassForm()
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class added!')
            return redirect('manage_classes')
    return render(request, 'portal/admin/class_form.html', {'form': form, 'title': 'Add Class'})


@login_required
def edit_class(request, pk):
    cls = get_object_or_404(Class, pk=pk)
    form = ClassForm(instance=cls)
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=cls)
        if form.is_valid():
            form.save()
            messages.success(request, 'Class updated!')
            return redirect('manage_classes')
    return render(request, 'portal/admin/class_form.html', {'form': form, 'title': 'Edit Class'})


@login_required
def manage_subjects(request):
    subjects = Subject.objects.select_related('student_class', 'teacher').all()
    return render(request, 'portal/admin/subjects.html', {'subjects': subjects})


@login_required
def add_subject(request):
    form = SubjectForm()
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added!')
            return redirect('manage_subjects')
    return render(request, 'portal/admin/subject_form.html', {'form': form, 'title': 'Add Subject'})


# ================== ATTENDANCE VIEWS ==================

@login_required
def mark_attendance(request):
    form = AttendanceForm()
    students = []
    if request.method == 'POST':
        if 'load_students' in request.POST:
            form = AttendanceForm(request.POST)
            if form.is_valid():
                cls = form.cleaned_data['student_class']
                students = Student.objects.filter(student_class=cls, is_active=True)
        elif 'save_attendance' in request.POST:
            date = request.POST.get('date')
            class_id = request.POST.get('class_id')
            cls = get_object_or_404(Class, pk=class_id)
            teacher = request.user.teacher if hasattr(request.user, 'teacher') else None
            student_ids = Student.objects.filter(student_class=cls, is_active=True).values_list('id', flat=True)
            for sid in student_ids:
                status = request.POST.get(f'status_{sid}', 'A')
                Attendance.objects.update_or_create(
                    student_id=sid, date=date,
                    defaults={'status': status, 'marked_by': teacher}
                )
            messages.success(request, 'Attendance saved!')
            return redirect('mark_attendance')
    return render(request, 'portal/teacher/mark_attendance.html', {'form': form, 'students': students})


@login_required
def view_attendance(request):
    role = get_user_role(request.user)
    if role == 'student':
        student = request.user.student
        records = Attendance.objects.filter(student=student).order_by('-date')
        total = records.count()
        present = records.filter(status='P').count()
        pct = round(present / total * 100, 1) if total > 0 else 0
        return render(request, 'portal/student/attendance.html', {
            'records': records, 'total': total, 'present': present, 'pct': pct
        })
    elif role == 'parent':
        student = request.user.parent.student
        records = Attendance.objects.filter(student=student).order_by('-date')
        total = records.count()
        present = records.filter(status='P').count()
        pct = round(present / total * 100, 1) if total > 0 else 0
        return render(request, 'portal/student/attendance.html', {
            'records': records, 'total': total, 'present': present, 'pct': pct, 'student': student
        })
    else:
        classes = Class.objects.all()
        selected_class = request.GET.get('class')
        selected_date = request.GET.get('date')
        records = []
        if selected_class and selected_date:
            records = Attendance.objects.filter(
                student__student_class_id=selected_class, date=selected_date
            ).select_related('student__user')
        return render(request, 'portal/teacher/view_attendance.html', {
            'classes': classes, 'records': records,
            'selected_class': selected_class, 'selected_date': selected_date
        })


# ================== MARKS VIEWS ==================

@login_required
def enter_marks(request):
    form = MarkForm()
    teacher = getattr(request.user, 'teacher', None)
    if teacher:
        form.fields['subject'].queryset = Subject.objects.filter(teacher=teacher)
        form.fields['student'].queryset = Student.objects.filter(
            student_class__in=teacher.classes.all())
    if request.method == 'POST':
        form = MarkForm(request.POST)
        if teacher:
            form.fields['subject'].queryset = Subject.objects.filter(teacher=teacher)
        if form.is_valid():
            mark = form.save(commit=False)
            mark.entered_by = teacher
            mark.save()
            messages.success(request, 'Marks saved!')
            return redirect('enter_marks')
    return render(request, 'portal/teacher/enter_marks.html', {'form': form})


@login_required
def view_marks(request):
    role = get_user_role(request.user)
    if role == 'student':
        student = request.user.student
        marks = Mark.objects.filter(student=student).select_related('subject', 'exam_type')
        exam_types = ExamType.objects.all()
        return render(request, 'portal/student/marks.html', {'marks': marks, 'exam_types': exam_types})
    elif role == 'parent':
        student = request.user.parent.student
        marks = Mark.objects.filter(student=student).select_related('subject', 'exam_type')
        return render(request, 'portal/student/marks.html', {'marks': marks, 'student': student})
    else:
        classes = Class.objects.all()
        students = Student.objects.none()
        marks = Mark.objects.none()
        selected_student = request.GET.get('student')
        if selected_student:
            marks = Mark.objects.filter(student_id=selected_student).select_related('subject', 'exam_type')
        return render(request, 'portal/teacher/view_marks.html', {
            'classes': classes, 'marks': marks
        })


# ================== TIMETABLE VIEW ==================

@login_required
def view_timetable(request):
    role = get_user_role(request.user)
    timetable = []
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    if role == 'student':
        cls = request.user.student.student_class
        timetable = Timetable.objects.filter(student_class=cls).select_related('subject', 'teacher__user')
    elif role == 'parent':
        cls = request.user.parent.student.student_class
        timetable = Timetable.objects.filter(student_class=cls).select_related('subject', 'teacher__user')
    elif role == 'teacher':
        teacher = request.user.teacher
        timetable = Timetable.objects.filter(teacher=teacher).select_related('subject', 'student_class')
    elif role == 'admin':
        selected_class = request.GET.get('class')
        classes = Class.objects.all()
        if selected_class:
            timetable = Timetable.objects.filter(student_class_id=selected_class).select_related('subject', 'teacher__user')
        form = TimetableForm()
        if request.method == 'POST':
            form = TimetableForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Timetable entry added!')
                return redirect('view_timetable')
        return render(request, 'portal/admin/timetable.html', {
            'timetable': timetable, 'days': days, 'classes': classes,
            'form': form, 'selected_class': selected_class
        })

    timetable_by_day = {day: [] for day in days}
    for entry in timetable:
        timetable_by_day[entry.day].append(entry)

    return render(request, 'portal/student/timetable.html', {
        'timetable_by_day': timetable_by_day, 'days': days
    })


# ================== FEE VIEWS ==================

@login_required
def manage_fees(request):
    role = get_user_role(request.user)
    if role in ['student']:
        fees = Fee.objects.filter(student=request.user.student)
    elif role == 'parent':
        fees = Fee.objects.filter(student=request.user.parent.student)
    else:
        fees = Fee.objects.select_related('student__user').all().order_by('-due_date')
    return render(request, 'portal/fees.html', {'fees': fees, 'role': role})


@login_required
def add_fee(request):
    form = FeeForm()
    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee record added!')
            return redirect('manage_fees')
    return render(request, 'portal/admin/fee_form.html', {'form': form})


# ================== NOTICE VIEWS ==================

@login_required
def notice_board(request):
    role = get_user_role(request.user)
    audience_map = {'admin': ['ALL', 'STU', 'TCH', 'PAR', 'ADM'],
                    'teacher': ['ALL', 'TCH'], 'student': ['ALL', 'STU'],
                    'parent': ['ALL', 'PAR']}
    audiences = audience_map.get(role, ['ALL'])
    notices = Notice.objects.filter(is_active=True, audience__in=audiences)
    return render(request, 'portal/notices.html', {'notices': notices, 'role': role})


@login_required
def add_notice(request):
    form = NoticeForm()
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.posted_by = request.user
            notice.save()
            messages.success(request, 'Notice posted!')
            return redirect('notice_board')
    return render(request, 'portal/admin/notice_form.html', {'form': form})


@login_required
def delete_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        notice.delete()
        messages.success(request, 'Notice deleted!')
        return redirect('notice_board')
    return render(request, 'portal/confirm_delete.html', {'obj': notice, 'type': 'Notice'})


# ================== LIBRARY VIEWS ==================

@login_required
def library(request):
    books = Book.objects.all()
    role = get_user_role(request.user)
    my_issues = []
    if role == 'student':
        my_issues = BookIssue.objects.filter(student=request.user.student).select_related('book')
    return render(request, 'portal/library.html', {'books': books, 'my_issues': my_issues, 'role': role})


@login_required
def add_book(request):
    form = BookForm()
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book added!')
            return redirect('library')
    return render(request, 'portal/admin/book_form.html', {'form': form})


@login_required
def issue_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if book.available_copies > 0:
        student_id = request.POST.get('student_id')
        due_date = request.POST.get('due_date')
        if student_id and due_date:
            BookIssue.objects.create(
                book=book, student_id=student_id,
                due_date=due_date, issued_by=request.user
            )
            book.available_copies -= 1
            book.save()
            messages.success(request, 'Book issued!')
    return redirect('library')


@login_required
def return_book(request, issue_id):
    issue = get_object_or_404(BookIssue, pk=issue_id)
    if request.method == 'POST':
        issue.return_date = timezone.now().date()
        issue.status = 'R'
        issue.book.available_copies += 1
        issue.book.save()
        issue.save()
        messages.success(request, 'Book returned!')
    return redirect('library')


# ================== HOMEWORK VIEWS ==================

@login_required
def homework(request):
    role = get_user_role(request.user)
    if role == 'student':
        hw = Homework.objects.filter(student_class=request.user.student.student_class)
    elif role == 'parent':
        hw = Homework.objects.filter(student_class=request.user.parent.student.student_class)
    elif role == 'teacher':
        hw = Homework.objects.filter(assigned_by=request.user.teacher)
    else:
        hw = Homework.objects.all()
    from datetime import date
    return render(request, 'portal/homework.html', {'homeworks': hw, 'role': role, 'today': date.today()})


@login_required
def add_homework(request):
    form = HomeworkForm()
    teacher = getattr(request.user, 'teacher', None)
    if teacher:
        form.fields['subject'].queryset = Subject.objects.filter(teacher=teacher)
        form.fields['student_class'].queryset = teacher.classes.all()
    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES)
        if teacher:
            form.fields['subject'].queryset = Subject.objects.filter(teacher=teacher)
        if form.is_valid():
            hw = form.save(commit=False)
            hw.assigned_by = teacher
            hw.save()
            messages.success(request, 'Homework assigned!')
            return redirect('homework')
    return render(request, 'portal/teacher/homework_form.html', {'form': form})


# ================== CLASS TEST VIEWS ==================

@login_required
def class_tests(request):
    role = get_user_role(request.user)
    if role == 'teacher':
        tests = ClassTest.objects.filter(created_by=request.user.teacher)
    elif role == 'student':
        student = request.user.student
        tests = ClassTest.objects.filter(student_class=student.student_class, is_active=True)
        attempted = TestAttempt.objects.filter(student=student).values_list('test_id', flat=True)
        for t in tests:
            t.attempted = t.id in attempted
    else:
        tests = ClassTest.objects.all()
    return render(request, 'portal/tests.html', {'tests': tests, 'role': role})


@login_required
def create_test(request):
    form = ClassTestForm()
    teacher = getattr(request.user, 'teacher', None)
    if teacher:
        form.fields['subject'].queryset = Subject.objects.filter(teacher=teacher)
        form.fields['student_class'].queryset = teacher.classes.all()
    if request.method == 'POST':
        form = ClassTestForm(request.POST)
        if teacher:
            form.fields['subject'].queryset = Subject.objects.filter(teacher=teacher)
        if form.is_valid():
            test = form.save(commit=False)
            test.created_by = teacher
            test.save()
            messages.success(request, 'Test created! Now add questions.')
            return redirect('add_questions', test_id=test.id)
    return render(request, 'portal/teacher/create_test.html', {'form': form})


@login_required
def add_questions(request, test_id):
    test = get_object_or_404(ClassTest, pk=test_id)
    form = QuestionForm()
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.test = test
            q.save()
            messages.success(request, 'Question added!')
            return redirect('add_questions', test_id=test_id)
    questions = test.questions.all()
    return render(request, 'portal/teacher/add_questions.html', {
        'test': test, 'form': form, 'questions': questions
    })


@login_required
def take_test(request, test_id):
    test = get_object_or_404(ClassTest, pk=test_id)
    student = request.user.student
    attempt, created = TestAttempt.objects.get_or_create(test=test, student=student)
    if attempt.is_submitted:
        return redirect('test_result', attempt_id=attempt.id)

    questions = test.questions.all()
    if request.method == 'POST':
        score = 0
        for q in questions:
            selected = request.POST.get(f'q_{q.id}', '')
            is_correct = selected == q.correct_answer
            if is_correct:
                score += q.marks
            StudentAnswer.objects.update_or_create(
                attempt=attempt, question=q,
                defaults={'selected_option': selected, 'is_correct': is_correct}
            )
        attempt.score = score
        attempt.is_submitted = True
        attempt.submitted_at = timezone.now()
        attempt.save()
        return redirect('test_result', attempt_id=attempt.id)
    return render(request, 'portal/student/take_test.html', {'test': test, 'questions': questions, 'attempt': attempt})


@login_required
def test_result(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, pk=attempt_id)
    answers = attempt.answers.select_related('question').all()
    pct = round(attempt.score / attempt.test.total_marks * 100, 1) if attempt.test.total_marks > 0 else 0
    return render(request, 'portal/student/test_result.html', {
        'attempt': attempt, 'answers': answers, 'pct': pct
    })


@login_required
def student_profile(request):
    role = get_user_role(request.user)
    if role == 'student':
        student = request.user.student
    elif role == 'parent':
        student = request.user.parent.student
    else:
        return redirect('dashboard')
    return render(request, 'portal/student/profile.html', {'student': student})


# ================== PROGRESS REPORT ==================

@login_required
def progress_report(request, student_id=None):
    role = get_user_role(request.user)
    if role == 'student':
        student = request.user.student
    elif role == 'parent':
        student = request.user.parent.student
    elif role in ['admin', 'teacher'] and student_id:
        student = get_object_or_404(Student, pk=student_id)
    else:
        return redirect('dashboard')

    exam_types = ExamType.objects.all()
    marks_data = {}
    subjects = Subject.objects.filter(student_class=student.student_class)

    for et in exam_types:
        marks_data[et.name] = {}
        for sub in subjects:
            try:
                m = Mark.objects.get(student=student, subject=sub, exam_type=et)
                marks_data[et.name][sub.name] = {
                    'marks': m.marks_obtained, 'max': m.max_marks,
                    'pct': m.percentage(), 'grade': m.grade()
                }
            except Mark.DoesNotExist:
                marks_data[et.name][sub.name] = None

    total_days = Attendance.objects.filter(student=student).count()
    present_days = Attendance.objects.filter(student=student, status='P').count()
    att_pct = round(present_days / total_days * 100, 1) if total_days > 0 else 0

    return render(request, 'portal/progress_report.html', {
        'student': student, 'exam_types': exam_types,
        'subjects': subjects, 'marks_data': marks_data,
        'total_days': total_days, 'present_days': present_days,
        'att_pct': att_pct, 'role': role
    })


@login_required
def all_students_progress(request):
    """Admin/Teacher view of all students in a class"""
    classes = Class.objects.all()
    selected_class_id = request.GET.get('class')
    students = []
    if selected_class_id:
        students = Student.objects.filter(student_class_id=selected_class_id).select_related('user')
        for s in students:
            total = Attendance.objects.filter(student=s).count()
            present = Attendance.objects.filter(student=s, status='P').count()
            s.att_pct = round(present / total * 100, 1) if total > 0 else 0
            s.avg_marks = Mark.objects.filter(student=s).aggregate(
                avg=Avg('marks_obtained'))['avg'] or 0
            s.avg_marks = round(float(s.avg_marks), 1)
    return render(request, 'portal/admin/all_progress.html', {
        'classes': classes, 'students': students, 'selected_class': selected_class_id
    })
