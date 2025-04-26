from django.db import models
from django.contrib.auth.models import User
from auctions.models import Auction
from django.utils import timezone

class FraudReport(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('confirmed', 'Confirmed Fraud'),
        ('dismissed', 'Dismissed'),
    )

    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='fraud_reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_frauds')
    reason = models.TextField(help_text='Describe why you think this auction is fraudulent')
    evidence = models.FileField(upload_to='fraud_evidence/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report #{self.id} - {self.auction.title}"

class FraudRiskScore(models.Model):
    auction = models.OneToOneField(Auction, on_delete=models.CASCADE, related_name='fraud_risk')
    score = models.FloatField(default=0.0, help_text='Fraud risk score (0-1)')
    features = models.JSONField(default=dict, help_text='Features used for fraud detection')
    last_updated = models.DateTimeField(default=timezone.now)
    is_flagged = models.BooleanField(default=False)
    admin_reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Risk Score for {self.auction.title}: {self.score:.2f}"

    @property
    def risk_level(self):
        if self.score < 0.3:
            return 'Low'
        elif self.score < 0.7:
            return 'Medium'
        else:
            return 'High'
