from django.db import models
from django.utils import timezone

from blogs.models import Blog

class BlogView(models.Model):
    blog = models.ForeignKey(Blog, related_name='views', on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True) # not using auto_now_add to allow custom timestamps during data seeding

    class Meta:
        db_table = "BlogView"

    def __str__(self):
        return f"{self.blog} - {self.ip_address} - {self.created_at}"
