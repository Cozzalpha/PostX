from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('create/', views.create_post, name='create_post'),
    path('approve/<int:post_id>/', views.approve_post, name='approve_post'),
    path('regenerate/<int:post_id>/', views.regenerate_caption, name='regenerate_caption'),
    path('edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('campaign/new/', views.create_campaign, name='create_campaign'),
    path('campaign/stop/<int:campaign_id>/', views.stop_campaign, name='stop_campaign'),
    path('post/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('campaign/delete/<int:campaign_id>/', views.delete_campaign, name='delete_campaign'),
    path('campaign/restart/<int:campaign_id>/', views.restart_campaign, name='restart_campaign'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
