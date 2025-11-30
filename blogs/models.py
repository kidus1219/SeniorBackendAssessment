from django.db import models
from django.conf import settings
from django.utils import timezone


class Blog(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now, db_index=True) # not using auto_now_add to allow custom timestamps during data seeding

    class Meta:
        db_table = "Blog"

    def __str__(self):
        return f"{self.title} - {self.author} - {self.created_at}"
