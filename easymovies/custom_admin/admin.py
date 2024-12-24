from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from movies_and_user.models import User, Movie, Review, Subscription, Package

class CustomUserAdmin(UserAdmin):
    model = User
    # Specify the fields to display in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser')
    # Specify which fields are editable in the admin
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('address', 'tel', 'profile_image')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('address', 'tel', 'profile_image')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Movie)
admin.site.register(Review)
admin.site.register(Subscription)
admin.site.register(Package)

