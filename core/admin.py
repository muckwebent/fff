from django.contrib import admin
from .models import User, Profile, HomeFeatures, Testimonials, Post

class UserAdmin(admin.ModelAdmin):
    search_fields  = ['full_name', 'username', 'email',  'phone']
    list_display  = ['full_name', 'username', 'email',  'phone']


class ProfileAdmin(admin.ModelAdmin):
    search_fields  = ['user', 'shop_name']
    list_display = ['thumbnail', 'user', 'full_name', 'verified']
class PostAdmin(admin.ModelAdmin):
    list_editable = ['user', 'title']
    list_display = ['thumbnail', 'user', 'title', ]
    prepopulated_fields = {"slug": ("title", )}


admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
# Register your models here.
admin.site.register(HomeFeatures)
admin.site.register(Testimonials)
admin.site.register(Post, PostAdmin)