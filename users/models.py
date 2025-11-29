from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    country = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return f"{self.first_name}"
