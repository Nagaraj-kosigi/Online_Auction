from django.urls import path
from . import views

app_name = 'fraud_detection'

urlpatterns = [
    path('report/<int:auction_id>/', views.report_fraud, name='report_fraud'),
    path('dashboard/', views.fraud_dashboard, name='dashboard'),
    path('scan/', views.scan_auctions, name='scan_auctions'),
    path('report/<int:report_id>/update/', views.update_report_status, name='update_report_status'),
]
