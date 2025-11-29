from django.db import models
from blogs.models import Blog

class BlogView(models.Model):
    blog = models.ForeignKey(Blog, related_name='views', on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "BlogView"

    def __str__(self):
        return f"{self.blog} - {self.ip_address} - {self.created_at}"
