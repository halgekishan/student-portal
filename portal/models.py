from django.db import models
from django.contrib.auth.models import User


class Class(models.Model):
    name = models.CharField(max_length=20)  # e.g. "Class 5"
    section = models.CharField(max_length=5, default='A')
    academic_year = models.CharField(max_length=10, default='2024-25')

    def __str__(self):
        return f"{self.name} - {self.section} ({self.academic_year})"

    class Meta:
        verbose_name_plural = "Classes"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=50)
    classes = models.ManyToManyField(Class, blank=True)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class Student(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True)
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    parent_name = models.CharField(max_length=100)
    parent_phone = models.CharField(max_length=15)
    admission_date = models.DateField(auto_now_add=True)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.roll_number})"


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='parents')
    relation = models.CharField(max_length=20, default='Parent')
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.get_full_name()} - Parent of {self.student}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    student_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='subjects')
    max_marks = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.name} ({self.student_class})"


class Attendance(models.Model):
    STATUS_CHOICES = [('P', 'Present'), ('A', 'Absent'), ('L', 'Late')]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    marked_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    remarks = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"


class ExamType(models.Model):
    name = models.CharField(max_length=50)  # e.g. "Term 1", "Half Yearly"
    academic_year = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.IntegerField(default=100)
    entered_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='entered_marks')
    entered_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'exam_type')

    def percentage(self):
        return round((self.marks_obtained / self.max_marks) * 100, 2)

    def grade(self):
        p = self.percentage()
        if p >= 90: return 'A+'
        elif p >= 80: return 'A'
        elif p >= 70: return 'B+'
        elif p >= 60: return 'B'
        elif p >= 50: return 'C'
        elif p >= 35: return 'D'
        return 'F'

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.marks_obtained}"


class Timetable(models.Model):
    DAYS = [('Mon','Monday'),('Tue','Tuesday'),('Wed','Wednesday'),
            ('Thu','Thursday'),('Fri','Friday'),('Sat','Saturday')]

    student_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    day = models.CharField(max_length=3, choices=DAYS)
    period_number = models.IntegerField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='timetable_entries')

    class Meta:
        unique_together = ('student_class', 'day', 'period_number')
        ordering = ['day', 'period_number']

    def __str__(self):
        return f"{self.student_class} - {self.day} P{self.period_number} - {self.subject}"


class Fee(models.Model):
    STATUS_CHOICES = [('P', 'Paid'), ('U', 'Unpaid'), ('PP', 'Partially Paid')]
    FEE_TYPES = [('T', 'Tuition'), ('E', 'Exam'), ('S', 'Sports'),
                 ('L', 'Library'), ('M', 'Miscellaneous')]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    fee_type = models.CharField(max_length=2, choices=FEE_TYPES)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='U')
    receipt_number = models.CharField(max_length=30, blank=True)
    academic_year = models.CharField(max_length=10)
    remarks = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.student} - {self.fee_type} - {self.status}"


class Notice(models.Model):
    AUDIENCE_CHOICES = [('ALL', 'All'), ('STU', 'Students'), ('TCH', 'Teachers'),
                        ('PAR', 'Parents'), ('ADM', 'Admin')]
    PRIORITY_CHOICES = [('H', 'High'), ('M', 'Medium'), ('L', 'Low')]

    title = models.CharField(max_length=200)
    content = models.TextField()
    audience = models.CharField(max_length=3, choices=AUDIENCE_CHOICES, default='ALL')
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='M')
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    posted_on = models.DateTimeField(auto_now_add=True)
    valid_till = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    attachment = models.FileField(upload_to='notice_attachments/', blank=True, null=True)

    class Meta:
        ordering = ['-posted_on']

    def __str__(self):
        return self.title


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=20, unique=True, blank=True)
    category = models.CharField(max_length=50)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    publisher = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.title} by {self.author}"


class BookIssue(models.Model):
    STATUS_CHOICES = [('I', 'Issued'), ('R', 'Returned'), ('O', 'Overdue')]

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='I')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fine_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.book} -> {self.student}"


class Homework(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    student_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='assigned_homeworks')
    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    attachment = models.FileField(upload_to='homework_files/', blank=True, null=True)

    class Meta:
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.title} - {self.subject}"


class ClassTest(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    student_class = models.ForeignKey(Class, on_delete=models.CASCADE)
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='created_tests')
    created_on = models.DateTimeField(auto_now_add=True)
    duration_minutes = models.IntegerField(default=30)
    total_marks = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.subject}"


class Question(models.Model):
    test = models.ForeignKey(ClassTest, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
    marks = models.IntegerField(default=1)

    def __str__(self):
        return f"Q{self.id}: {self.question_text[:50]}"


class TestAttempt(models.Model):
    test = models.ForeignKey(ClassTest, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('test', 'student')

    def __str__(self):
        return f"{self.student} - {self.test} - {self.score}"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('attempt', 'question')
