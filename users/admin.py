from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import Group
from .models import User, Country


class UserAdmin(DefaultUserAdmin):
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "first_name", "last_name", "email", "is_active", "is_staff", "is_superuser", "user_permissions",),
            },
        ),
    )

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "user_permissions")
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    readonly_fields = ("last_login", "date_joined")
    list_display = ('username', 'first_name', 'last_name', 'last_login' ,'date_joined')
    list_filter = ('date_joined', 'is_active', 'is_staff', 'is_superuser')
    ordering = ('-date_joined',)


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Country)
