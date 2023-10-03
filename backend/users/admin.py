from django.contrib import admin

from users.models import Follow, User


admin.site.register(Follow)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_superuser',
    )
    search_fields = ('email', 'username')
