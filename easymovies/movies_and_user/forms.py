from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Movie, Review, Subscription, Package

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'username','first_name','last_name', 'password1', 'password2', 'address', 'tel', 'profile_image']

class MovieForm(forms.ModelForm):
     class Meta:
        model = Movie
        fields = [
            'title', 'release_date', 'total_views', 'rating', 'category', 
            'director', 'actors', 'genre', 'video_file', 'description','thumbnail', 'cover_image'
        ]
        widgets = {
            'release_date': forms.DateInput(attrs={'type': 'date'}),
            'actors': forms.Textarea(attrs={'rows': 3}),
            'genre': forms.TextInput(attrs={'placeholder': 'e.g., Action, Sci-Fi'}),
            'rating': forms.NumberInput(attrs={'step': 0.1, 'min': 0, 'max': 5}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'commentary']
        
class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = '__all__'

class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ['package_name', 'package_price', 'streaming_quality', 'device_limit', 'content_access_level', 'is_trial', 'duration_in_days', 'parental_controls']


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email Address")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No user with this email found.")
        return email