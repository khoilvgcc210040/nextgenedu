from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=10, null=True, blank=True)
    grade = models.CharField(max_length=10, null=True, blank=True)
    terms_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} - {self.grade}"
