from django.urls import path
from . import views


app_name = 'analytics'
urlpatterns = [
    path('blog-views/', views.BlogViewsAnalytics.as_view(), name='blog_views'),
]
