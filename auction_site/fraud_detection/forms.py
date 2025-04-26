from django import forms
from .models import FraudReport

class FraudReportForm(forms.ModelForm):
    class Meta:
        model = FraudReport
        fields = ['reason', 'evidence']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'evidence': forms.FileInput(attrs={'class': 'form-control'})
        }
        help_texts = {
            'reason': 'Please explain why you believe this auction is fraudulent.',
            'evidence': 'Upload any screenshots or evidence (optional).'
        }
