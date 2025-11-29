from django.contrib import admin
from django.conf import settings
from django.http import JsonResponse
from django.urls import path, include, re_path
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('analytics/', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


def custom_404(request, exception):
    return JsonResponse({
        "status": 0,
        "message": "The requested resource was not found.",
        "data": None
    }, status=404)


def custom_500(request):
    return JsonResponse({
        "status": 0,
        "message": "An unexpected error occurred.",
        "data": None
    }, status=500)


handler404 = 'main.urls.custom_404'
handler500 = 'main.urls.custom_500'
