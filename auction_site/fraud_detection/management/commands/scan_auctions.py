from django.core.management.base import BaseCommand
from fraud_detection.services import FraudDetectionService
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scan auctions for potential fraud'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Scan auctions created in the last N hours (default: 24)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Scan all active auctions, not just recent ones'
        )
    
    def handle(self, *args, **options):
        start_time = time.time()
        fraud_service = FraudDetectionService()
        
        if options['all']:
            self.stdout.write(self.style.WARNING('Scanning all active auctions...'))
            count = fraud_service.scan_all_auctions()
            self.stdout.write(self.style.SUCCESS(f'Scanned {count} auctions'))
        else:
            hours = options['hours']
            self.stdout.write(self.style.WARNING(f'Scanning auctions from the last {hours} hours...'))
            count = fraud_service.scan_new_auctions(hours=hours)
            self.stdout.write(self.style.SUCCESS(f'Scanned {count} auctions'))
        
        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f'Completed in {elapsed_time:.2f} seconds'))
