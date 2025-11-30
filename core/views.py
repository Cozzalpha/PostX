from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Post, Client, Campaign, CampaignImage
from .forms import PostForm, CampaignForm
import google.generativeai as genai
from core.tasks import GEMINI_API_KEY, generate_ai_content, initialize_campaign_posts

@login_required
def dashboard(request):
    """
    Shows Active Campaigns AND Recent Single Posts.
    """
    if request.user.is_superuser:
        posts = Post.objects.all().order_by('scheduled_time') # Ascending order for timeline
        campaigns = Campaign.objects.all().order_by('-is_active')
        is_admin = True
    else:
        try:
            client_profile = request.user.client_profile
            posts = Post.objects.filter(client=client_profile).order_by('scheduled_time')
            campaigns = Campaign.objects.filter(client=client_profile)
            is_admin = False
        except:
            return render(request, 'base.html', {'content': 'No Client Profile Found'})

    return render(request, 'dashboard.html', {
        'posts': posts, 
        'campaigns': campaigns, 
        'is_admin': is_admin
    })

@login_required
def create_post(request):
    """Create a Single Scheduled Post"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            
            if request.user.is_superuser:
                post.client = Client.objects.first()
            else:
                post.client = request.user.client_profile
            
            # CHECK DRAFT STATUS
            is_draft = form.cleaned_data.get('save_as_draft')
            
            if is_draft:
                post.status = 'draft'
                post.save()
            else:
                post.status = 'scheduled'
                post.save()
                # Trigger AI immediately
                generate_ai_content.delay(post.id)
                
            return redirect('dashboard')
    else:
        form = PostForm()
    
    return render(request, 'post_form.html', {'form': form, 'page_title': 'Create New Single Post'})

@login_required
def create_campaign(request):
    """Create a Recurring Campaign"""
    if request.method == 'POST':
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save(commit=False)
            
            if request.user.is_superuser:
                campaign.client = Client.objects.first()
            else:
                campaign.client = request.user.client_profile
                
            campaign.save()
            
            # --- HANDLE MULTIPLE IMAGES ---
            images = request.FILES.getlist('campaign_images')
            for img in images:
                CampaignImage.objects.create(campaign=campaign, image=img)
            
            # 🔥 CALL THE NEW GENERATOR
            # This generates the roadmap for the WHOLE campaign range immediately
            initialize_campaign_posts.delay(campaign.id)
            
            return redirect('dashboard')
    else:
        form = CampaignForm()
    return render(request, 'create_campaign.html', {'form': form})

@login_required
def stop_campaign(request, campaign_id):
    """Stops the auto-scheduler for this campaign"""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    if not request.user.is_superuser and campaign.client.user != request.user:
        return redirect('dashboard')
        
    campaign.is_active = False
    campaign.save()
    return redirect('dashboard')

@login_required
def restart_campaign(request, campaign_id):
    """Re-activate a stopped campaign"""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    if not request.user.is_superuser and campaign.client.user != request.user:
        return redirect('dashboard')
    
    campaign.is_active = True
    campaign.save()
    return redirect('dashboard')

@login_required
def delete_campaign(request, campaign_id):
    """Permanently delete a campaign"""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    if not request.user.is_superuser and campaign.client.user != request.user:
        return redirect('dashboard')
    
    campaign.delete()
    return redirect('dashboard')

@login_required
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.status = 'approved'
    post.save()
    return redirect('dashboard')

@login_required
def regenerate_caption(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    genai.configure(api_key=GEMINI_API_KEY)
    # Switch to 1.5 if 2.5 fails for you
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""You are a senior Social Media Manager for {post.client.company_name}
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
    post.generated_caption = response.text.replace('Here is a caption:', '').strip('"')
    post.save()
    return redirect('dashboard')

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        new_caption = request.POST.get('generated_caption')
        post.generated_caption = new_caption
        post.save()
        return redirect('dashboard')
    
    return render(request, 'edit_post.html', {'post': post})

@login_required
def delete_post(request, post_id):
    """Permanently delete a post"""
    post = get_object_or_404(Post, id=post_id)
    if not request.user.is_superuser and post.client.user != request.user:
        return redirect('dashboard')
    
    post.delete()
    return redirect('dashboard')