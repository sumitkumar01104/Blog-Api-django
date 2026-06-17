from django.contrib import admin
from .models import Post
# Register your models here.

admin.site.site_header = 'SUMIT NAGAR'
admin.site.site_title = 'Blog'
admin.site.index_title = 'Welcome To Blog App'

@admin.register(Post)
class Admin(admin.ModelAdmin):
    list_display = ['title','author']
    search_fields = ['title']
