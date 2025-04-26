from django.db.models.signals import post_save
from django.dispatch import receiver
from auctions.models import Auction
from .services import FraudDetectionService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Auction)
def scan_new_auction(sender, instance, created, **kwargs):
    """
    Signal handler to automatically scan new auctions for fraud
    """
    if created:
        try:
            logger.info(f"Scanning new auction: {instance.title} (ID: {instance.id})")
            fraud_service = FraudDetectionService()
            risk_score = fraud_service.predict_fraud_risk(instance)
            logger.info(f"Fraud risk score for auction {instance.id}: {risk_score.score:.2f}")
        except Exception as e:
            logger.error(f"Error scanning auction {instance.id}: {e}")
