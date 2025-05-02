from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Auction, Bid, UserProfile

class AuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['title', 'description', 'starting_price', 'image', 'category', 'end_date']
        widgets = {
            'end_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set minimum end date to 1 hour from now
        min_date = timezone.now() + timedelta(hours=1)
        # Set maximum end date to 30 days from now
        max_date = timezone.now() + timedelta(days=30)

        # Format dates for datetime-local input
        min_date_str = min_date.strftime('%Y-%m-%dT%H:%M')
        max_date_str = max_date.strftime('%Y-%m-%dT%H:%M')

        # Update widget attributes
        self.fields['end_date'].widget.attrs.update({
            'min': min_date_str,
            'max': max_date_str,
        })

        # Add help text
        self.fields['end_date'].help_text = 'Set when your auction will end (between 1 hour and 30 days from now)'

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        now = timezone.now()

        # Ensure end date is in the future (at least 1 hour)
        min_end_date = now + timedelta(hours=1)
        if end_date < min_end_date:
            raise forms.ValidationError('End date must be at least 1 hour in the future.')

        # Ensure end date is not too far in the future (max 30 days)
        max_end_date = now + timedelta(days=30)
        if end_date > max_end_date:
            raise forms.ValidationError('End date cannot be more than 30 days in the future.')

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']

    def __init__(self, *args, auction=None, user=None, **kwargs):
        self.auction = auction
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= self.auction.current_price:
            raise forms.ValidationError("Your bid must be higher than the current price.")
        return amount

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)

        # Update user email
        if commit and 'email' in self.cleaned_data:
            profile.user.email = self.cleaned_data['email']
            profile.user.save()

        if commit:
            profile.save()

        return profile

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Your current password is incorrect.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', "The two password fields didn't match.")

        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data.get('new_password1')
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('There is no user registered with this email address.')
        return email

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        label='Enter the 6-digit OTP sent to your email',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={'placeholder': '6-digit OTP', 'class': 'form-control'})
    )

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')
        if not otp.isdigit():
            raise forms.ValidationError('OTP should contain only digits')
        return otp