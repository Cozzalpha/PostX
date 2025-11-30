from django import forms
from .models import Post, Campaign

# Custom Widget to allow multiple file selection
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class PostForm(forms.ModelForm):
    save_as_draft = forms.BooleanField(
        required=False, 
        initial=False, 
        label="Save as Draft",
        widget=forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-indigo-600 rounded'})
    )

    image = forms.ImageField(
        required=True,
        widget=forms.ClearableFileInput(attrs={'class': 'w-full p-2 border rounded-lg'})
    )

    class Meta:
        model = Post
        fields = ['news_update', 'image', 'scheduled_time', 'requires_approval']
        widgets = {
            'news_update': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg', 'rows': 4, 'placeholder': 'What is this post about?'}),
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full p-3 border rounded-lg'}),
            'requires_approval': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-indigo-600 rounded'}),
        }
class CampaignForm(forms.ModelForm):
    campaign_images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={'class': 'w-full p-3 border rounded-lg bg-white'})
    )

    class Meta:
        model = Campaign
        fields = ['name', 'type', 'topic_prompt', 'posts_per_day', 'start_date', 'end_date', 'daily_start_time', 'interval_hours', 'auto_approve', 'campaign_images']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'type': forms.Select(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'topic_prompt': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg', 'rows': 3}),
            'posts_per_day': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'daily_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full p-3 border rounded-lg'}),
            'interval_hours': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3 border rounded-lg'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3 border rounded-lg'}),
            
            # THE NEW CHECKBOX
            'auto_approve': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-indigo-600 rounded'}),
        }