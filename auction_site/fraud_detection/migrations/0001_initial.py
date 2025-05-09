# Generated by Django 5.1.7 on 2025-04-23 18:49

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auctions', '0005_alter_bid_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FraudReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(help_text='Describe why you think this auction is fraudulent')),
                ('evidence', models.FileField(blank=True, null=True, upload_to='fraud_evidence/')),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('investigating', 'Under Investigation'), ('confirmed', 'Confirmed Fraud'), ('dismissed', 'Dismissed')], default='pending', max_length=20)),
                ('admin_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('auction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fraud_reports', to='auctions.auction')),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reported_frauds', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FraudRiskScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(default=0.0, help_text='Fraud risk score (0-1)')),
                ('features', models.JSONField(default=dict, help_text='Features used for fraud detection')),
                ('last_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_flagged', models.BooleanField(default=False)),
                ('admin_reviewed', models.BooleanField(default=False)),
                ('auction', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fraud_risk', to='auctions.auction')),
            ],
        ),
    ]
