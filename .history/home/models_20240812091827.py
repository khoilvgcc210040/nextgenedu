from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=10, null=True, blank=True)
    grade = models.CharField(max_length=10, null=True, blank=True)
    terms_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} - {self.grade}"

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
    
class Classroom(models.Model):
    name = models.CharField(max_length=200)
    subject = models.ForeignKey(Subjects, on_delete=models.CASCADE)
    grade = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    school = models.TextField(max_length=200, default="N/A")
    status = models.BooleanField(default=False)
    password = models.TextField(max_length=20, null=True, blank=True)
    participants = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject.name} - Grade {self.grade}"