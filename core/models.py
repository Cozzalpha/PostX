from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    company_name = models.CharField(max_length=100)
    company_bio = models.TextField()
    instagram_access_token = models.CharField(max_length=500)
    instagram_business_id = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='client_logos/', blank=True, null=True)
    def __str__(self): return self.company_name

class Campaign(models.Model):
    CAMPAIGN_TYPES = [
        ('topic', 'Specific Topic Series'),
        ('bio', 'General Brand Awareness'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES)
    topic_prompt = models.TextField(blank=True)
    
    # Scheduling
    posts_per_day = models.IntegerField(default=3)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    daily_start_time = models.TimeField(default=datetime.time(9, 0))
    interval_hours = models.IntegerField(default=2)
    
    # NEW: The Auto-Post Switch
    auto_approve = models.BooleanField(default=False, help_text="If checked, posts will be published without your review.")
    
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class CampaignImage(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='campaign_pool/')

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled (Waiting for AI)'),
        ('generating', 'Generating AI...'),
        ('waiting_approval', 'AI Done (Needs Review)'),
        ('approved', 'Approved (Queue to Post)'),
        ('publishing', 'Publishing in Progress...'), # <--- ADD THIS
        ('posted', 'Posted'),
        ('error', 'Error'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    news_update = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    scheduled_time = models.DateTimeField()
    requires_approval = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    generated_caption = models.TextField(blank=True, null=True)
    
    def __str__(self): return f"{self.client.company_name} - {self.status}"