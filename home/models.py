from django.contrib.auth.models import AbstractUser
from django.db import models
from django.forms import ValidationError
from django.utils import timezone

class Subjects(models.Model):
    GRADE_CHOICES = [
        (10, '10'),
        (11, '11'),
        (12, '12'),
    ]

    name = models.CharField(max_length=200)
    grade = models.IntegerField(choices=GRADE_CHOICES, default=10)
    description = models.TextField()
    bg_color = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} - {self.grade}"

class CustomUser(AbstractUser):
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=10, null=True, blank=True)
    grade = models.CharField(max_length=10, null=True, blank=True)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE, null=True, blank=True)
    notify_sections = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} - {self.grade}"
    
class AcademicYear(models.Model):
    open_year = models.IntegerField()
    close_year = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.open_year}-{self.close_year}"
    
class Classroom(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='classrooms', null=True, blank=True)
    name = models.CharField(max_length=200)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    grade = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    school = models.TextField(max_length=200, default="N/A")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
    status = models.BooleanField(default=False)
    password = models.TextField(max_length=20, null=True, blank=True)
    likes = models.IntegerField(default=0)
    allow_chat = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {self.subject.name} - Grade {self.grade} - {self.status}"
    
    def clean(self):
        if self.status and (not self.password or len(self.password) < 6):
            raise ValidationError('Password must be at least 6 characters long if the classroom is private.')

    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('teacher', 'name')

class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    rating = models.IntegerField(null=True, blank=True)  # Allow null for subsequent comments
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.classroom.name}"

    class Meta:
        unique_together = ('user', 'classroom', 'rating')  # Ensure one rating per classroom per user


class Section(models.Model):
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    parent_section = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subsections')
    description = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.title} - {self.classroom.name}'
    
class SubsectionFile(models.Model):
    subsection = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='subsection_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.subsection.title} - {self.file.name}"

    
class Submission(models.Model):
    SUBMISSION_TYPES = [
        ('assignment', 'Assignment'),
        ('question_test', 'Question Test'),
    ]
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='submissions')
    title = models.CharField(max_length=200)
    submission_type = models.CharField(max_length=50, choices=SUBMISSION_TYPES)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    open_date = models.DateTimeField()
    close_date = models.DateTimeField()

    def is_open(self):
        now = timezone.now()
        return self.open_date <= now <= self.close_date
    
    def not_open_yet(self):
        now = timezone.now()
        return now < self.open_date

    def closed(self):
        now = timezone.now()
        return now > self.close_date


    def __str__(self):
        return self.title
    
class SubmissionFile(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='submission_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.submission.title} - {self.file.name}"

    
class StudentFile(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='student_files')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='student_files')
    file = models.FileField(upload_to='student_files/')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.username} - {self.submission.title}'
    
class Participant(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='participants')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='participants')
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    
class Question(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question: {self.text[:50]}" 


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)  

    def __str__(self):
        return f"Answer: {self.text[:50]}"
    
class QuizResult(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='quiz_results')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_results')
    correct_answers = models.IntegerField(default=0)  # Giá trị mặc định là 0
    answered_questions = models.IntegerField(default=1)
    total_questions = models.IntegerField(default=0)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    time_taken = models.DurationField(null=True, blank=True)
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.submission.title} - Score: {self.score}"
    
    @property
    def is_question_test(self):
        return self.submission.submission_type == 'question_test'

class AnsweredQuestion(models.Model):
    quiz_result = models.ForeignKey(QuizResult, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.quiz_result.student.username} - {self.question.submission.title} - Question: {self.question.text[:50]}"
    
class ChatMessage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    message = models.TextField()
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True) 
    file = models.FileField(upload_to='chat_files/', null=True, blank=True) 
    timestamp = models.DateTimeField(auto_now_add=True)
    file_size = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]} - {self.classroom.name}"
    
    @property
    def is_file(self):
        return self.file is not None

    @property
    def is_image(self):
        return self.image is not None
    
class FavoriteClassroom(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favorite_classrooms')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'classroom')

    def __str__(self):
        return f"{self.user.username} - {self.classroom.name}"
    
class BlockedParticipant(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    blocked_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.classroom.name}"

