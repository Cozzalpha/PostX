from celery import shared_task
from django.utils import timezone
from .models import Post, Campaign
import google.generativeai as genai
import requests
import time
import random
from datetime import timedelta
from datetime import timedelta, datetime
from django.core.files.base import ContentFile

# --- CONFIGURATION ---
# ⚠️ REPLACE THIS WITH YOUR ACTUAL API KEY
GEMINI_API_KEY = "upload it here"
NGROK_URL = "https://janessa-unwedded-forrest.ngrok-free.dev"
genai.configure(api_key=GEMINI_API_KEY)

@shared_task
def check_schedule():
    """Heartbeat: Only checks for AI Generation or Publishing."""
    now = timezone.now()
    
    # 1. Trigger AI for Scheduled Posts
    # Mark as 'generating' immediately to prevent double-AI
    drafts = Post.objects.filter(status='scheduled', scheduled_time__lte=now)
    for post in drafts:
        post.status = 'generating' # <--- LOCK 1
        post.save()
        generate_ai_content.delay(post.id)

    # 2. Publish Approved Posts
    # Mark as 'publishing' immediately to prevent double-posting
    ready = Post.objects.filter(status='approved', scheduled_time__lte=now)
    for post in ready:
        print(f"🔒 Locking Post #{post.id} to prevent double-post...")
        post.status = 'publishing' # <--- LOCK 2
        post.save()
        upload_to_facebook.delay(post.id)

@shared_task
def initialize_campaign_posts(campaign_id):
    """
    Generates ALL posts for the ENTIRE duration of the campaign immediately.
    Fixes the 'Duplicate' bug and 'Date' issue.
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        print(f"🚀 Initializing Campaign: {campaign.name}")
        
        # Get Images from the Campaign Pool
        campaign_images = list(campaign.images.all())
        
        # Determine Logic
        MARKETING_ANGLES = ["Values", "Unique Selling Point", "Customer Success", "Behind the Scenes", "Call to Action"]
        
        # LOOP THROUGH DATES
        current_date = campaign.start_date
        while current_date <= campaign.end_date:
            
            # Create Base Time for this specific day
            base_time_str = f"{current_date} {campaign.daily_start_time}"
            base_time = datetime.strptime(base_time_str, "%Y-%m-%d %H:%M:%S")
            # Make it timezone aware (Important for Django)
            base_time = timezone.make_aware(base_time)

            for i in range(campaign.posts_per_day):
                # Calculate specific time for this post
                post_time = base_time + timedelta(hours=(i * campaign.interval_hours))
                
                # Content Logic
                if campaign.type == 'topic':
                    news_text = f"Series '{campaign.name}' - Post {i+1}: {campaign.topic_prompt}"
                else:
                    angle = MARKETING_ANGLES[i % len(MARKETING_ANGLES)]
                    news_text = f"General Awareness ({angle})"

                # Create the Post Object
                new_post = Post(
                    client=campaign.client,
                    campaign=campaign,
                    news_update=news_text,
                    scheduled_time=post_time,
                    # INHERIT APPROVAL SETTING from Campaign
                    requires_approval=not campaign.auto_approve, 
                    status='scheduled' # Ready for AI to pick it up when time comes
                )
                
                # Assign Image (Shuffle Logic)
                if campaign_images:
                    chosen_image = random.choice(campaign_images)
                    # Duplicate the file so if campaign is deleted, post image remains
                    new_post.image.save(chosen_image.image.name, chosen_image.image.file, save=False)
                
                # If no images, we leave it empty (fallback to Logo later)
                
                new_post.save()
                
                # OPTIONAL: Trigger AI immediately for ALL posts (so user can review now)
                # If you comment this out, AI will generate them day-by-day.
                generate_ai_content.delay(new_post.id)

            # Move to next day
            current_date += timedelta(days=1)
            
    except Exception as e:
        print(f"Campaign Error: {e}")

@shared_task
def generate_ai_content(post_id):
    """
    TRIGGERED IMMEDIATELY upon creation (unless Draft).
    """
    try:
        post = Post.objects.get(id=post_id)
        
        # Skip if it's a draft
        if post.status == 'draft':
            return

        post.status = 'generating'
        post.save()

        # Build Prompt based on Context
        # Note: If 2.5 fails, switch back to 'gemini-1.5-flash'
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # --- NEW DETAILED PROMPT ---
        prompt = f"""
        You are a senior Social Media Manager for {post.client.company_name}.
        
        COMPANY BIO:
        {post.client.company_bio}
        
        TOPIC/NEWS FOR THIS POST:
        {post.news_update}
        
        TASK:
        Write a high-engaging Instagram caption using the AIDA framework.
        Include 3-5 emojis and end with 5 hashtags.
        
        KEEP THESE GUIDELINES IN MIND:
        1. Strong Opening Hook: The first sentence is crucial. Ask a question, state a surprising fact, create urgency/FOMO, or use provocative language.
        2. Clarity and Conciseness: Get straight to the point. Use simple language, maybe bullet points, and keep paragraphs short (1-2 sentences).
        3. Provide Value: Educate, inspire, entertain, or solve a problem.
        4. Call to Action (CTA): Tell the audience exactly what to do next (Comment, Share, Link in Bio, Tag a friend).
        5. Tone and Personality: Be authentic, conversational, and use emojis to convey emotion. Avoid sounding like a corporate bot.
        6. Searchability: Use strategic hashtags.

        ⚠️ STRICT OUTPUT RULES (DO NOT IGNORE):
        1. Return ONLY the final caption text.
        2. Do NOT add introductions like "Here is a caption" or "Sure!".
        3. Do NOT add quotes "" around the text.
        4. Start the response immediately with the hook/headline.
        """
        
        response = model.generate_content(prompt)
        
        # Extra safety cleanup (just in case AI ignores rule #3)
        clean_caption = response.text.replace('Here is a caption:', '').strip().strip('"')
        
        post.generated_caption = clean_caption
        
        # Logic remains exactly the same as before
        if post.requires_approval:
            post.status = 'waiting_approval'
        else:
            post.status = 'approved'
            
        post.save()

    except Exception as e:
        print(f"AI Error: {e}")
        post.status = 'error'
        post.save()



@shared_task
def upload_to_facebook(post_id):
    """
    Uploads to Instagram.
    Includes Fallback Logic: If no Post Image, use Client Logo.
    """
    try:
        post = Post.objects.get(id=post_id)
        print(f"🚀 Starting Upload for Post #{post.id}...")

        # --- IMAGE SELECTION LOGIC ---
        if post.image:
            image_url = f"{NGROK_URL}{post.image.url}"
            print(f"📸 Using Custom Post Image.")
        elif post.client.logo:
            image_url = f"{NGROK_URL}{post.client.logo.url}"
            print(f"⚠️ No custom image. Using Client Logo as fallback.")
        else:
            raise Exception("❌ No Image! Post has no image and Client has no Logo.")

        access_token = post.client.instagram_access_token
        page_id = post.client.instagram_business_id
        
        # 1. Step 1: Create Container
        print(f"📤 Uploading image URL: {image_url}")
        url_create = f"https://graph.facebook.com/v21.0/{page_id}/media"
        payload_create = {
            'image_url': image_url,
            'caption': post.generated_caption,
            'access_token': access_token
        }
        
        r1 = requests.post(url_create, data=payload_create)
        data1 = r1.json()
        
        if 'id' not in data1:
            raise Exception(f"Facebook Container Error: {data1}")
            
        container_id = data1['id']
        print(f"📦 Container ID: {container_id}")

        # 2. Wait for processing
        print("⏳ Waiting 15 seconds for processing...")
        time.sleep(15)

        # 3. Step 2: Publish Container
        url_publish = f"https://graph.facebook.com/v21.0/{page_id}/media_publish"
        payload_publish = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        r2 = requests.post(url_publish, data=payload_publish)
        data2 = r2.json()
        
        if 'id' not in data2:
            raise Exception(f"Facebook Publish Error: {data2}")

        # 4. Success
        print(f"🎉 SUCCESS! Post Published ID: {data2['id']}")
        post.status = 'posted'
        post.save()

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        post.status = 'error'
        post.save()
