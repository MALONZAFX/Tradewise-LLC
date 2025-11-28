from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Affiliate, Referral

User = get_user_model()

@receiver(post_save, sender=User)
def create_affiliate_profile(sender, instance, created, **kwargs):
    """
    Automatically create an affiliate profile when a new user is created
    """
    if created:
        Affiliate.objects.get_or_create(user=instance)

# ❌ NO MORE BROKEN REFERRAL SIGNAL! ❌

@receiver(pre_save, sender=User)
def handle_user_referral(sender, instance, **kwargs):
    """
    Handle user registration with referral code
    """
    if instance.pk is None:  # New user being created
        # Check if there's a referral code in the session or request
        pass