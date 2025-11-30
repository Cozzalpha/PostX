from django.contrib import admin
from .models import Client, Post, Campaign

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user')

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'type', 'posts_per_day', 'is_active')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('client', 'status', 'scheduled_time', 'campaign')
    list_filter = ('status', 'client', 'campaign')