from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    
    
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]

    GRADE_CHOICES = [
        (10, '10'),
        (11, '11'),
        (12, '12'),
    ]
    
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True, blank=True)
    grade = models.CharField(max_length=10, choices=GRADE_CHOICES, null=True, blank=True)
    terms_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} - {self.grade}"
