from django import forms
from .models import Coaching, Strategy, Signal

class CoachingForm(forms.ModelForm):
    class Meta:
        model = Coaching
        fields = ['title', 'description', 'duration', 'price']

class StrategyForm(forms.ModelForm):
    class Meta:
        model = Strategy
        fields = ['title', 'description', 'image', 'price_usd', 'price_kes', 'stats']

class SignalForm(forms.ModelForm):
    class Meta:
        model = Signal
        fields = ['title', 'description', 'image', 'price_usd', 'price_kes', 'accuracy_forex', 'accuracy_crypto', 'is_active']

