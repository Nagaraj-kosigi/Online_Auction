import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os
from django.conf import settings
from .models import FraudRiskScore
from auctions.models import Auction, User
import logging
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class FraudDetectionService:
    """Service for detecting potentially fraudulent auctions"""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_path = os.path.join(settings.BASE_DIR, 'fraud_detection', 'ml_models', 'fraud_model.pkl')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'fraud_detection', 'ml_models', 'scaler.pkl')
        self.load_or_train_model()

    def load_or_train_model(self):
        """Load the model if it exists, otherwise train a new one"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded existing fraud detection model")
            else:
                self.train_model()
        except Exception as e:
            logger.error(f"Error loading fraud detection model: {e}")
            self.train_model()

    def train_model(self):
        """Train a new fraud detection model using existing data"""
        logger.info("Training new fraud detection model")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        # For initial training, we'll use a simple model with synthetic data
        # In a real application, you would use historical data of confirmed frauds

        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000

        # Features: price_ratio, user_age_days, description_length, has_images,
        # previous_auctions, bid_count, category_risk
        X = np.random.rand(n_samples, 7)

        # Generate synthetic labels (0: legitimate, 1: fraud)
        # Higher chance of fraud if:
        # - price_ratio is very low (too good to be true)
        # - user is very new
        # - description is very short
        # - no images
        # - user has no previous auctions
        # - few or no bids
        # - high risk category

        fraud_indicators = (
            (X[:, 0] < 0.3) &  # Low price ratio
            (X[:, 1] < 0.2) &  # New user
            (X[:, 2] < 0.3) &  # Short description
            (X[:, 3] < 0.5) &  # No images
            (X[:, 4] < 0.2) &  # Few previous auctions
            (X[:, 5] < 0.3) &  # Few bids
            (X[:, 6] > 0.7)    # High risk category
        )

        # Add some randomness
        y = np.random.binomial(1, 0.1, size=n_samples)  # Base 10% fraud rate
        y[fraud_indicators] = np.random.binomial(1, 0.8, size=fraud_indicators.sum())  # 80% fraud if indicators present

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_scaled, y)

        # Save model and scaler
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

        logger.info("Fraud detection model trained and saved")

    def extract_features(self, auction):
        """Extract features from an auction for fraud detection"""
        try:
            # Get user account age in days
            user_created = auction.created_by.date_joined
            user_age_days = (timezone.now() - user_created).days

            # Calculate price ratio (current price / starting price)
            # A very low ratio might indicate a "too good to be true" situation
            price_ratio = 1.0  # Default
            if auction.starting_price > 0:
                price_ratio = float(auction.current_price) / float(auction.starting_price)

            # Description length (normalized)
            desc_length = len(auction.description) / 1000  # Normalize by 1000 chars

            # Check if auction has images
            has_images = 1 if auction.image else 0

            # Count previous auctions by this user
            previous_auctions = Auction.objects.filter(
                created_by=auction.created_by,
                start_date__lt=auction.start_date
            ).count()
            previous_auctions = min(previous_auctions / 10, 1.0)  # Normalize

            # Count bids
            bid_count = auction.bids.filter(status='active').count()
            bid_count = min(bid_count / 5, 1.0)  # Normalize

            # Category risk (some categories might be more prone to fraud)
            # This would ideally be based on historical data
            category_risk = 0.5  # Default medium risk
            high_risk_categories = ['Electronics', 'Jewelry', 'Luxury']
            if auction.category and auction.category.name in high_risk_categories:
                category_risk = 0.8

            # Return features as a dictionary for transparency
            features = {
                'price_ratio': price_ratio,
                'user_age_days': min(user_age_days / 365, 1.0),  # Normalize by 1 year
                'description_length': desc_length,
                'has_images': has_images,
                'previous_auctions': previous_auctions,
                'bid_count': bid_count,
                'category_risk': category_risk
            }

            return features

        except Exception as e:
            logger.error(f"Error extracting features for auction {auction.id}: {e}")
            # Return default features
            return {
                'price_ratio': 1.0,
                'user_age_days': 0.5,
                'description_length': 0.5,
                'has_images': 0,
                'previous_auctions': 0,
                'bid_count': 0,
                'category_risk': 0.5
            }

    def predict_fraud_risk(self, auction):
        """Predict the fraud risk for an auction"""
        try:
            # Extract features
            features = self.extract_features(auction)

            # Convert to array for prediction
            X = np.array([list(features.values())])

            # Scale features
            X_scaled = self.scaler.transform(X)

            # Predict probability of fraud
            fraud_prob = self.model.predict_proba(X_scaled)[0, 1]

            # Update or create risk score
            risk_score, created = FraudRiskScore.objects.update_or_create(
                auction=auction,
                defaults={
                    'score': fraud_prob,
                    'features': features,
                    'last_updated': timezone.now(),
                    'is_flagged': fraud_prob >= 0.7  # Flag high-risk auctions
                }
            )

            return risk_score

        except Exception as e:
            logger.error(f"Error predicting fraud risk for auction {auction.id}: {e}")
            return None

    def scan_all_auctions(self):
        """Scan all active auctions for fraud risk"""
        active_auctions = Auction.objects.filter(is_active=True)

        for auction in active_auctions:
            self.predict_fraud_risk(auction)

        return len(active_auctions)

    def scan_new_auctions(self, hours=24):
        """Scan auctions created in the last X hours"""
        time_threshold = timezone.now() - timedelta(hours=hours)
        new_auctions = Auction.objects.filter(
            start_date__gte=time_threshold,
            is_active=True
        )

        for auction in new_auctions:
            self.predict_fraud_risk(auction)

        return len(new_auctions)
