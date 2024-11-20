from django.contrib import admin
from django.contrib.auth.models import User
from .models import Post

# User Management
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'date_joined']
    search_fields = ['username', 'email']

# Content Management
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
