from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid
import os
from django.conf import settings
from django.urls import reverse
from .storage import MediaStorage

# Create custom storage instance
media_storage = MediaStorage(location=settings.MEDIA_ROOT)

def get_default_end_date():
    """
    Default end date is 7 days from now, but users can customize this
    when creating an auction (between 1 hour and 30 days)
    """
    return timezone.now() + timedelta(days=7)

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Auction(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='auction_images/', blank=True, null=True, storage=media_storage)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='auctions')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auctions')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='won_auctions', null=True, blank=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=get_default_end_date)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.current_price:
            self.current_price = self.starting_price
        super().save(*args, **kwargs)

    @property
    def time_remaining(self):
        if self.end_date > timezone.now():
            return self.end_date - timezone.now()
        return timedelta(0)

    @property
    def has_ended(self):
        return self.end_date < timezone.now()

class Bid(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    )

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    scheduled_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.bidder.username} bid {self.amount} on {self.auction.title}"

    def is_active(self):
        return self.status == 'active'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='profile_images/', blank=True, null=True, storage=media_storage)
    email_verified = models.BooleanField(default=False)
    email_verification_otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def is_otp_valid(self):
        if not self.email_verification_otp or not self.otp_expiry:
            return False
        return timezone.now() <= self.otp_expiry