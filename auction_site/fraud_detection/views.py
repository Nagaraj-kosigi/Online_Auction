from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import FraudReport, FraudRiskScore
from auctions.models import Auction
from .services import FraudDetectionService
from .forms import FraudReportForm

@login_required
def report_fraud(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    # Check if user has already reported this auction
    existing_report = FraudReport.objects.filter(
        auction=auction,
        reported_by=request.user
    ).exists()

    if existing_report:
        messages.warning(request, "You have already reported this auction.")
        return redirect('auction_detail', auction_id=auction.id)

    if request.method == 'POST':
        form = FraudReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.auction = auction
            report.reported_by = request.user
            report.save()

            # Run fraud detection on this auction
            fraud_service = FraudDetectionService()
            fraud_service.predict_fraud_risk(auction)

            messages.success(request, "Thank you for your report. Our team will review it shortly.")
            return redirect('auction_detail', auction_id=auction.id)
    else:
        form = FraudReportForm()

    return render(request, 'fraud_detection/report_fraud.html', {
        'form': form,
        'auction': auction
    })

@staff_member_required
def fraud_dashboard(request):
    # Get fraud statistics
    total_reports = FraudReport.objects.count()
    pending_reports = FraudReport.objects.filter(status='pending').count()
    confirmed_frauds = FraudReport.objects.filter(status='confirmed').count()

    # Get high risk auctions
    high_risk_auctions = FraudRiskScore.objects.filter(score__gte=0.7, is_flagged=True)

    # Get recent reports
    recent_reports = FraudReport.objects.order_by('-created_at')[:10]

    return render(request, 'fraud_detection/dashboard.html', {
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'confirmed_frauds': confirmed_frauds,
        'high_risk_auctions': high_risk_auctions,
        'recent_reports': recent_reports
    })

@staff_member_required
@require_POST
def scan_auctions(request):
    fraud_service = FraudDetectionService()
    count = fraud_service.scan_all_auctions()

    messages.success(request, f"Scanned {count} auctions for fraud risk.")
    return redirect('fraud_dashboard')

@staff_member_required
@require_POST
def update_report_status(request, report_id):
    report = get_object_or_404(FraudReport, id=report_id)
    status = request.POST.get('status')
    notes = request.POST.get('notes', '')

    if status in dict(FraudReport.STATUS_CHOICES).keys():
        report.status = status
        report.admin_notes = notes
        report.save()

        # If confirmed as fraud, delete the auction and notify the creator
        if status == 'confirmed':
            auction = report.auction
            auction_creator = auction.created_by
            auction_title = auction.title

            # Send email notification to the auction creator
            subject = 'Your Auction Has Been Removed Due to Fraud Detection'
            html_message = render_to_string('fraud_detection/email/fraud_confirmed_email.html', {
                'user': auction_creator,
                'auction_title': auction_title,
                'admin_notes': notes if notes else 'Our team has determined this auction violates our policies.',
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
                messages.success(request, f'Email notification sent to {auction_creator.email}')
            except Exception as e:
                messages.error(request, f'Failed to send email: {str(e)}')

            # Update risk score before deleting
            risk_score, _ = FraudRiskScore.objects.get_or_create(auction=auction)
            risk_score.score = 1.0  # Maximum risk
            risk_score.is_flagged = True
            risk_score.admin_reviewed = True
            risk_score.save()

            # Delete the auction
            auction.delete()
            messages.success(request, f'Auction "{auction_title}" has been deleted.')

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid status'})
