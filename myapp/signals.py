from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model  # Use this instead of direct import
from .models import Affiliate, Referral

# Get the correct user model for your project
User = get_user_model()

@receiver(post_save, sender=User)
def create_affiliate_profile(sender, instance, created, **kwargs):
    """
    Automatically create an affiliate profile when a new user is created
    """
    if created:
        Affiliate.objects.get_or_create(user=instance)

@receiver(post_save, sender=Referral)
def handle_referral_approval(sender, instance, created, **kwargs):
    """
    Handle affiliate stats when a referral is approved
    """
    if instance.status == 'approved':
        # Check if we've already processed this referral
        if not hasattr(instance, '_processed'):
            affiliate = instance.referrer
            affiliate.total_referrals += 1
            affiliate.total_coins_earned += instance.coins_earned
            affiliate.coin_balance += instance.coins_earned
            affiliate.save()
            
            # Mark as processed to avoid infinite loops
            instance._processed = True

@receiver(pre_save, sender=User)
def handle_user_referral(sender, instance, **kwargs):
    """
    Handle user registration with referral code
    """
    if instance.pk is None:  # New user being created
        # Check if there's a referral code in the session or request
        # You'll need to implement this based on your registration flow
        pass