from django.apps import AppConfig


class FraudDetectionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fraud_detection'

    def ready(self):
        import fraud_detection.signals
