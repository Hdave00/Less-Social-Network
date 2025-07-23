from django.contrib import admin
from .models import User, Post

# Register your models here.

# if we wish to see all aspects of a User in the admin interface, we can create a new class within admin.py and add it as an argument
# when registering the User model:
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email',)

class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content', 'timestamp',)


admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)
