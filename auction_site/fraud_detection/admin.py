from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.db import models
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import FraudReport, FraudRiskScore
from auctions.models import Auction
from .admin_site import fraud_admin_site
from .services import FraudDetectionService

class FraudReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'auction_link', 'reported_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('auction__title', 'reported_by__username', 'reason')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Report Information', {
            'fields': ('auction', 'reported_by', 'reason', 'evidence')
        }),
        ('Status', {
            'fields': ('status', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        # Check if status was changed to 'confirmed'
        if change and 'status' in form.changed_data and obj.status == 'confirmed':
            # Get the auction before saving the report
            auction = obj.auction
            auction_creator = auction.created_by
            auction_title = auction.title

            # Save the report first
            super().save_model(request, obj, form, change)

            # Send email notification to the auction creator
            from django.core.mail import send_mail
            from django.conf import settings
            from django.template.loader import render_to_string
            from django.utils.html import strip_tags

            subject = 'Your Auction Has Been Removed Due to Fraud Detection'
            html_message = render_to_string('fraud_detection/email/fraud_confirmed_email.html', {
                'user': auction_creator,
                'auction_title': auction_title,
                'admin_notes': obj.admin_notes if obj.admin_notes else 'Our team has determined this auction violates our policies.',
            })
            plain_message = strip_tags(html_message)

            try:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [auction_creator.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                self.message_user(request, f'Email notification sent to {auction_creator.email}')
            except Exception as e:
                self.message_user(request, f'Failed to send email: {str(e)}', level=messages.ERROR)

            # Update risk score before deleting
            from .models import FraudRiskScore
            risk_score, _ = FraudRiskScore.objects.get_or_create(auction=auction)
            risk_score.score = 1.0  # Maximum risk
            risk_score.is_flagged = True
            risk_score.admin_reviewed = True
            risk_score.save()

            # Delete the auction
            auction.delete()
            self.message_user(request, f'Auction "{auction_title}" has been deleted.')
        else:
            super().save_model(request, obj, form, change)

    def auction_link(self, obj):
        url = f'/admin/auctions/auction/{obj.auction.id}/change/'
        return format_html('<a href="{}">{}</a>', url, obj.auction.title)

    auction_link.short_description = 'Auction'

class FraudRiskScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'auction_link', 'score_display', 'risk_level', 'is_flagged', 'admin_reviewed', 'last_updated')
    list_filter = ('is_flagged', 'admin_reviewed', 'last_updated')
    search_fields = ('auction__title',)
    readonly_fields = ('auction', 'score', 'features', 'last_updated', 'risk_level_display')
    fieldsets = (
        ('Auction Information', {
            'fields': ('auction', 'score', 'risk_level_display')
        }),
        ('Features', {
            'fields': ('features',),
            'classes': ('collapse',)
        }),
        ('Admin Actions', {
            'fields': ('is_flagged', 'admin_reviewed')
        }),
        ('Timestamps', {
            'fields': ('last_updated',)
        }),
    )

    def auction_link(self, obj):
        url = f'/admin/auctions/auction/{obj.auction.id}/change/'
        return format_html('<a href="{}">{}</a>', url, obj.auction.title)

    def score_display(self, obj):
        color = 'green'
        if obj.score >= 0.3 and obj.score < 0.7:
            color = 'orange'
        elif obj.score >= 0.7:
            color = 'red'

        return format_html('<span style="color: {}; font-weight: bold;">{:.2f}</span>', color, obj.score)

    def risk_level_display(self, obj):
        color_map = {
            'Low': 'green',
            'Medium': 'orange',
            'High': 'red'
        }
        color = color_map.get(obj.risk_level, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.risk_level)

    auction_link.short_description = 'Auction'
    score_display.short_description = 'Fraud Score'
    risk_level_display.short_description = 'Risk Level'


# Add scan_auctions URL to the admin site
def scan_auctions_view(request):
    if request.method == 'POST':
        fraud_service = FraudDetectionService()
        count = fraud_service.scan_all_auctions()
        messages.success(request, f'Successfully scanned {count} auctions for fraud.')
    return redirect('/fraud-admin/')

# Add the URL pattern to the admin site
original_get_urls = fraud_admin_site.get_urls

def custom_get_urls():
    return [
        path('scan_auctions/', fraud_admin_site.admin_view(scan_auctions_view), name='scan_auctions'),
    ] + original_get_urls()

fraud_admin_site.get_urls = custom_get_urls


# Register models with the custom admin site
fraud_admin_site.register(FraudReport, FraudReportAdmin)
fraud_admin_site.register(FraudRiskScore, FraudRiskScoreAdmin)
fraud_admin_site.register(Auction, admin.ModelAdmin)  # Basic view of auctions

# Custom admin site is configured in admin_site.py
