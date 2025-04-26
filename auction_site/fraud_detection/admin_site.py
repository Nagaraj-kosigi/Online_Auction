from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse

from django.urls import path, reverse
from django.http import HttpResponseRedirect

class FraudAdminSite(AdminSite):
    site_header = _('Auction Fraud Detection')
    site_title = _('Auction Fraud Admin')
    index_title = _('Fraud Management Dashboard')

    def index(self, request, extra_context=None):
        """
        Override the default index to use our custom template
        """
        # Get fraud statistics
        from .models import FraudReport, FraudRiskScore
        from auctions.models import Auction
        from django.utils import timezone
        from datetime import timedelta

        total_reports = FraudReport.objects.count()
        pending_reports = FraudReport.objects.filter(status='pending').count()
        investigating_reports = FraudReport.objects.filter(status='investigating').count()
        confirmed_frauds = FraudReport.objects.filter(status='confirmed').count()
        dismissed_reports = FraudReport.objects.filter(status='dismissed').count()

        # Get risk statistics
        total_auctions = Auction.objects.filter(is_active=True).count()
        high_risk = FraudRiskScore.objects.filter(score__gte=0.7).count()
        medium_risk = FraudRiskScore.objects.filter(score__gte=0.3, score__lt=0.7).count()
        low_risk = FraudRiskScore.objects.filter(score__lt=0.3).count()

        # Get recent reports
        recent_reports = FraudReport.objects.order_by('-created_at')[:10]

        # Get high risk auctions
        high_risk_auctions = FraudRiskScore.objects.filter(score__gte=0.7).order_by('-score')[:10]

        # Get report trend (last 7 days)
        today = timezone.now().date()
        report_trend = []
        for i in range(7):
            day = today - timedelta(days=i)
            count = FraudReport.objects.filter(
                created_at__date=day
            ).count()
            report_trend.append({
                'date': day.strftime('%d %b'),
                'count': count
            })
        report_trend.reverse()

        context = {
            **self.each_context(request),
            'title': self.index_title,
            'total_reports': total_reports,
            'pending_reports': pending_reports,
            'investigating_reports': investigating_reports,
            'confirmed_frauds': confirmed_frauds,
            'dismissed_reports': dismissed_reports,
            'total_auctions': total_auctions,
            'high_risk': high_risk,
            'medium_risk': medium_risk,
            'low_risk': low_risk,
            'recent_reports': recent_reports,
            'high_risk_auctions': high_risk_auctions,
            'report_trend': report_trend,
            **(extra_context or {}),
        }

        request.current_app = self.name

        return TemplateResponse(request, 'admin/fraud_detection/dashboard.html', context)

    def app_index(self, request, app_label, extra_context=None):
        """
        Redirect app index to the main index
        """
        return HttpResponseRedirect(reverse('%s:index' % self.name))

    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_list = super().get_app_list(request)

        # Move fraud_detection to the top
        for i, app in enumerate(app_list):
            if app['app_label'] == 'fraud_detection':
                app_list.insert(0, app_list.pop(i))
                break

        return app_list

fraud_admin_site = FraudAdminSite(name='fraud_admin')
