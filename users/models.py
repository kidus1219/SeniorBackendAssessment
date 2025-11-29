from django.contrib.auth.models import AbstractUser
from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)

    class Meta:
        db_table = "Country"

    def __str__(self):
        return self.name


class User(AbstractUser):
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.first_name}"
