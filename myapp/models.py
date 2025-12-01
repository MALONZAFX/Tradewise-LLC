# myapp/models.py
from django.db import models
from django.template.loader import render_to_string
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from django.db import transaction
import uuid
import os
import requests
import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
import json
# ================== PAYSTACK PAYMENT SERVICE ==================

class PaystackService:
    """Paystack payment service integration"""
    def __init__(self):
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        self.public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
        self.base_url = "https://api.paystack.co"
    
    def initialize_transaction(self, email, amount, reference, callback_url=None, metadata=None):
        """Initialize Paystack transaction"""
        url = f"{self.base_url}/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "email": email,
            "amount": amount,  # Amount in kobo
            "reference": reference,
        }
        
        if callback_url:
            data["callback_url"] = callback_url
            
        if metadata:
            data["metadata"] = metadata
            
        try:
            print(f"📡 Sending request to Paystack: {url}")
            print(f"📡 Headers: {headers}")
            print(f"📡 Data: {data}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            print(f"📡 Paystack response status: {response.status_code}")
            print(f"📡 Paystack response content: {response.text}")
            
            return response.json()
        except requests.exceptions.Timeout:
            print("❌ Paystack request timeout")
            return {"status": False, "message": "Request timeout"}
        except requests.exceptions.RequestException as e:
            print(f"❌ Paystack request error: {str(e)}")
            return {"status": False, "message": str(e)}
        except Exception as e:
            print(f"❌ Paystack general error: {str(e)}")
            return {"status": False, "message": str(e)}
    
    def verify_transaction(self, reference):
        """Verify Paystack transaction"""
        url = f"{self.base_url}/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            return response.json()
        except requests.exceptions.Timeout:
            return {"status": False, "message": "Request timeout"}
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": str(e)}
        except Exception as e:
            return {"status": False, "message": str(e)}

# ================== CORE USER MODELS ==================

class Tradeviewusers(models.Model):
    """Main user model for TradeWise platform"""
    first_name = models.CharField(max_length=50)
    second_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    
    account_number = models.PositiveIntegerField(unique=True, default=0)
    phone = models.CharField(max_length=20, blank=True, null=True)
    plan = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            last_user = Tradeviewusers.objects.order_by('-account_number').first()
            self.account_number = 5000 if not last_user else last_user.account_number + 1
        
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
            
        if not self.pk and not self.email_verification_token:
            self.email_verification_token = secrets.token_urlsafe(32)
            
        # Auto-set admin status for specific account numbers
        if self.account_number in [500100, 500200]:
            self.is_admin = True
            self.is_staff = True
            
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def can_access_admin(self):
        """Check if user can access admin dashboard"""
        return self.is_admin and self.account_number in [500100, 500200]

    def send_verification_email(self):
        """Send email verification - FIXED LOCALHOST URL"""
        try:
            print(f"🟢 MODEL: Starting verification email for {self.email}")
            
            if not self.email_verification_token:
                self.email_verification_token = secrets.token_urlsafe(32)
                self.save()
            
            subject = '✅ Verify Your TradeWise Account'
            
            # ✅ FIXED: Use proper localhost URL
            verification_url = f"https://www.tradewise-hub.com/verify-email/{self.email_verification_token}/"
            
            print(f"🔗 LOCALHOST VERIFICATION URL: {verification_url}")
            
            # Check if template exists
            try:
                html_message = render_to_string('emails/verification_email.html', {
                    'user': self,
                    'verification_url': verification_url,
                })
                print(f"✅ MODEL: verification_email.html template found")
            except Exception as e:
                print(f"❌ MODEL: Template error: {e}")
                html_message = f"""
                <h2>Verify Your TradeWise Account</h2>
                <p>Hello {self.first_name},</p>
                <p>Click here to verify: <a href="{verification_url}">Verify Email</a></p>
                """
            
            plain_message = f"""
Dear {self.first_name},

Welcome to TradeWise! Please verify your email address to activate your account.

Your Account Details:
- Name: {self.first_name} {self.second_name}
- TradeWise Number: {self.account_number}
- Email: {self.email}

Click the link below to verify your email:
{verification_url}

Best regards,
TradeWise Team
            """
            
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[self.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            print(f"✅ MODEL: Verification email sent - Result: {result}")
            print(f"📍 VERIFICATION LINK: {verification_url}")
            return True
            
        except Exception as e:
            print(f"❌ MODEL: Verification email failed: {str(e)}")
            return False

    def send_welcome_email(self, password):
        """Send welcome email - NEW METHOD"""
        try:
            print(f"🟢 MODEL: Starting welcome email for {self.email}")
            
            subject = '🎉 Welcome to TradeWise - Account Created Successfully!'
            
            try:
                html_message = render_to_string('emails/welcome_email.html', {
                    'user': self,
                    'password': password,
                })
                print(f"✅ MODEL: welcome_email.html template found")
            except Exception as e:
                print(f"❌ MODEL: Welcome template error: {e}")
                html_message = f"""
                <h2>Welcome to TradeWise!</h2>
                <p>Hello {self.first_name}, your account was created successfully!</p>
                <p>Account Number: {self.account_number}</p>
                <p>Temporary Password: {password}</p>
                """
            
            plain_message = f"""
Welcome to TradeWise, {self.first_name}!

Your account has been created successfully.

Account Details:
- Name: {self.first_name} {self.second_name}
- TradeWise Number: {self.account_number}
- Email: {self.email}
- Temporary Password: {password}

Please change your password after first login.

Best regards,
TradeWise Team
            """
            
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[self.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            print(f"✅ MODEL: Welcome email sent - Result: {result}")
            return True
            
        except Exception as e:
            print(f"❌ MODEL: Welcome email failed: {str(e)}")
            return False

    def send_new_user_notification(self):
        """Send admin notification - NEW METHOD"""
        try:
            print(f"🟢 MODEL: Starting admin notification for new user {self.email}")
            
            subject = '👤 New User Registration - TradeWise'
            
            try:
                html_message = render_to_string('emails/new_user.html', {
                    'user': self,
                })
                print(f"✅ MODEL: new_user.html template found")
            except Exception as e:
                print(f"❌ MODEL: New user template error: {e}")
                html_message = f"""
                <h2>New User Registered</h2>
                <p>Name: {self.first_name} {self.second_name}</p>
                <p>Email: {self.email}</p>
                <p>Account: {self.account_number}</p>
                """
            
            plain_message = f"""
New User Registration:

Name: {self.first_name} {self.second_name}
TradeWise Number: {self.account_number}
Email: {self.email}
Phone: {self.phone}
Registered: {self.created_at.strftime('%Y-%m-%d %H:%M')}
            """
            
            admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[admin_email],
                html_message=html_message,
                fail_silently=False,
            )
            
            print(f"✅ MODEL: Admin notification sent - Result: {result}")
            return True
            
        except Exception as e:
            print(f"❌ MODEL: Admin notification failed: {str(e)}")
            return False

    def send_password_reset_email(self):
        """Send password reset email - FIXED LOCALHOST URL"""
        try:
            print(f"🟢 MODEL: Starting password reset email for {self.email}")
            
            if not self.password_reset_token:
                self.password_reset_token = secrets.token_urlsafe(32)
                self.save()
            
            subject = '🔐 Reset Your TradeWise Password'
            
            # ✅ FIXED: Use localhost for password reset too
            reset_url = f"https://www.tradewise-hub.com/reset-password/{self.password_reset_token}/"
            
            html_message = render_to_string('emails/password_reset.html', {
                'user': self,
                'reset_url': reset_url,
            })
            
            plain_message = f"""
Password Reset Request

Hello {self.first_name},

You requested to reset your password. Click the link below:

{reset_url}

If you didn't request this, please ignore this email.

Best regards,
TradeWise Team
            """
            
            result = send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[self.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            print(f"✅ MODEL: Password reset email sent - Result: {result}")
            return True
            
        except Exception as e:
            print(f"❌ MODEL: Password reset email failed: {str(e)}")
            return False

    def __str__(self):
        return f"{self.first_name} {self.second_name} (TWN: {self.account_number})"

    class Meta:
        verbose_name = "TradeView User"
        verbose_name_plural = "TradeView Users"


class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(Tradeviewusers, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    
    # Trading preferences
    trading_experience = models.CharField(max_length=50, blank=True, null=True)
    preferred_markets = models.JSONField(default=list, blank=True)
    risk_tolerance = models.CharField(max_length=20, blank=True, null=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.first_name} {self.user.second_name}"
    
# ================== CONTENT MANAGEMENT MODELS ==================

class TradeWiseCard(models.Model):
    """TradeWise membership card details"""
    title = models.CharField(max_length=200, default='TradeWise Premium')
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    card_number = models.CharField(max_length=50, default='6734 559')
    capital_available = models.CharField(max_length=50, default='$500,000')
    partner_name = models.CharField(max_length=100, default='SPALIS FX')
    contact_number = models.CharField(max_length=20, default='+254742962615')
    image = models.ImageField(upload_to='cards/', blank=True, null=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=49.99)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=499.99)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "TradeWise Membership Card"

class Service(models.Model):
    """Services offered by TradeWise"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, default='fas fa-chart-line')
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    features = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['display_order', 'title']

class PricingPlan(models.Model):
    """Pricing plans for trading packages"""
    PLAN_TYPES = [
        ('starter', 'Starter'),
        ('pro', 'Professional'),
        ('vip', 'VIP'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='custom')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    description = models.TextField()
    features = models.JSONField(default=list)
    is_highlighted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    duration_days = models.IntegerField(default=30)
    display_order = models.IntegerField(default=0)
    color_scheme = models.CharField(max_length=50, default='#0056b3')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pricing Plan"
        verbose_name_plural = "Pricing Plans"
        ordering = ['display_order', 'price']
    
    def __str__(self):
        return f"{self.name} - KES {self.price}"

class Merchandise(models.Model):
    CATEGORIES = [
        ('caps-hats', 'Caps & Hats'),
        ('hoodies', 'Hoodies'), 
        ('t-shirts', 'T-Shirts'),
        ('accessories', 'Accessories'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='t-shirts')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='merchandise/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=True)  # ALL ITEMS ARE FEATURED BY DEFAULT!
    stock_quantity = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

class Review(models.Model):
    """Client reviews and testimonials"""
    # Name fields for compatibility
    client_name = models.CharField(max_length=100, blank=True, null=True)
    author_name = models.CharField(max_length=100, blank=True, null=True)  # NEW FIELD
    user_role = models.CharField(max_length=100, default='Forex Trader')  # RENAMED from profession
    email = models.EmailField(blank=True, null=True)  # NEW FIELD
    
    # Review content
    content = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    image = models.ImageField(upload_to='reviews/', blank=True, null=True)
    
    # Status fields
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    from_admin = models.BooleanField(default=False)  # NEW FIELD
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_image_url(self):
        """Safely get image URL with fallback"""
        if self.image and hasattr(self.image, 'url') and self.image.url:
            return self.image.url
        return '/static/images/default-avatar.jpg'

    def save(self, *args, **kwargs):
        # Handle backward compatibility
        if self.client_name and not self.author_name:
            self.author_name = self.client_name
        elif self.author_name and not self.client_name:
            self.client_name = self.author_name
            
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.author_name or self.client_name or "Anonymous"
        return f"Review by {name} - {self.rating} stars"

    class Meta:
        ordering = ['-is_featured', '-created_at']

class BlogPost(models.Model):
    """Blog posts for TradeWise"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    author = models.CharField(max_length=100, default='TradeWise Team')
    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

class TradeWiseCoin(models.Model):
    """TradeWise Coin information"""
    title = models.CharField(max_length=200, default='TradeWise Coin')
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField()
    price = models.CharField(max_length=100, default='$0.10 per TWC (Limited Supply)')
    bonus_text = models.CharField(max_length=200, default='Early investors get +15% bonus tokens in the first round.')
    image = models.ImageField(upload_to='coin/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class AffiliateProgram(models.Model):
    """Affiliate program information"""
    title = models.CharField(max_length=200, default='TradeWise Affiliate Program')
    description = models.TextField()
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    weekly_number = models.CharField(max_length=20, default='500100')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# ================== TRADING PRODUCTS MODELS ==================

class TradingStrategy(models.Model):
    """Trading strategies for sale"""
    # EXISTING FIELDS (keep these)
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='strategies/', blank=True, null=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NEW FIELDS TO ADD FOR FRONTEND TEMPLATE
    MARKET_TYPES = [
        ('forex', 'Forex'),
        ('crypto', 'Cryptocurrency'),
        ('stocks', 'Stocks'),
        ('commodities', 'Commodities'),
        ('indices', 'Indices'),
        ('all', 'All Markets'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all', 'All Levels'),
    ]
    
    STRATEGY_TYPES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
    ]
    
    # Add these new fields
    market_type = models.CharField(
        max_length=20, 
        choices=MARKET_TYPES, 
        default='all',
        help_text="Which market this strategy is designed for"
    )
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='all',
        help_text="Experience level required for this strategy"
    )
    
    strategy_type = models.CharField(
        max_length=20,
        choices=STRATEGY_TYPES,
        default='free',
        help_text="Free, Premium, or VIP strategy"
    )
    
    is_featured = models.BooleanField(
        default=False,
        help_text="Featured strategies appear first"
    )
    
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this strategy was viewed"
    )
    
    # Meta information
    class Meta:
        verbose_name_plural = "Trading Strategies"
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.title

class TradingSignal(models.Model):
    # EXISTING FIELDS (keep these)
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='signals/', blank=True, null=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # NEW FIELDS FOR SIGNALS TEMPLATE
    SIGNAL_TYPES = [
        ('forex', 'Forex'),
        ('crypto', 'Cryptocurrency'),
        ('stocks', 'Stocks'),
        ('all', 'All Markets'),
    ]
    
    signal_type = models.CharField(
        max_length=20,
        choices=SIGNAL_TYPES,
        default='forex',
        help_text="Type of trading signals"
    )
    
    accuracy_forex = models.PositiveIntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Forex accuracy percentage (0-100)"
    )
    
    accuracy_crypto = models.PositiveIntegerField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Crypto accuracy percentage (0-100)"
    )
    
    is_featured = models.BooleanField(
        default=False,
        help_text="Featured signals appear first"
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-is_featured', '-created_at']

class PaymentService(models.Model):
    """Payment services offered"""
    SERVICE_CATEGORIES = [
        ('copy_trading', 'Copy Trading'),
        ('live_trading', 'Live Trading'),
        ('signals', 'Trading Signals'),
        ('education', 'Trading Education'),
        ('funding', 'Account Funding'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES)
    description = models.TextField()
    price_label = models.CharField(max_length=100, help_text="e.g., 'Starting from $50'")
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"

# ================== SERVICE REQUEST MODELS ==================

class ServiceRequest(models.Model):
    """Unified service request model"""
    SERVICE_TYPES = [
        ('copy_trading', 'Copy Trading'),
        ('live_trading', 'Live Trading'),
        ('capital_funding', 'Capital Funding'),
        ('consultation', 'Consultation'),
        ('coaching', 'Coaching'),
        ('general', 'General Service'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES, default='general') 
    service_details = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(Tradeviewusers, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_service_type_display()} - {self.name}"

# ================== PAYMENT MODELS ==================




# ================== SERVICE PAYMENT MODELS ==================    
class ServicePayment(models.Model):
    """NEW: For tracking trading service payments (Copy Trading, Live Trading, etc.)"""
    SERVICE_TYPES = [
        ('copy_trading', 'Copy Trading'),
        ('live_trading', 'Live Trading Sessions'), 
        ('trading_signals', 'Trading Signals'),
        ('consultation', '1-on-1 Consultation'),
        ('capital_funding', 'Capital Funding'),
        ('advanced_course', 'Advanced Trading Course'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic info
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField()
    user_phone = models.CharField(max_length=20)
    
    # Service details
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    email_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_progress(self, payment_amount):
        """Update payment progress"""
        self.amount_paid += payment_amount
        self.progress_percentage = (self.amount_paid / self.total_amount) * 100
        
        if self.progress_percentage >= 100:
            self.status = 'completed'
            if not self.email_sent:
                self.send_onboarding_email()
                self.email_sent = True
        elif self.progress_percentage > 0:
            self.status = 'in_progress'
            
        self.save()

    def send_onboarding_email(self):
        """Send email when service is fully paid"""
        subject = f'🎉 Your {self.get_service_type_display()} is Ready!'
        
        message = f"""
Dear {self.user_name},

Your {self.get_service_type_display()} service is now fully paid and activated!

Total Paid: KES {self.amount_paid}
Service: {self.get_service_type_display()}

You can now access your service. We'll contact you shortly with next steps.

Best regards,
TradeWise Team
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[self.user_email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Service email error: {str(e)}")
            return False

    def __str__(self):
        return f"{self.user_email} - {self.get_service_type_display()} - {self.progress_percentage}%"

class ServiceTransaction(models.Model):
    """NEW: Individual payments for services"""
    service_payment = models.ForeignKey(ServicePayment, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='pending')
    paystack_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Service TX: {self.reference} - KES {self.amount}"




# ================== AFFILIATE MODELS - FIXED VERSION ==================

class Affiliate(models.Model):
    """Affiliate program - COMPLETELY UPDATED FOR AUTO-COIN AWARDS"""
    user = models.OneToOneField(Tradeviewusers, on_delete=models.CASCADE, related_name='affiliate')
    referral_code = models.CharField(max_length=20, unique=True)
    total_referrals = models.PositiveIntegerField(default=0)
    total_coins_earned = models.PositiveIntegerField(default=0)
    coin_balance = models.PositiveIntegerField(default=0)
    total_payouts = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Affiliate: {self.user.first_name} {self.user.second_name} (Balance: {self.coin_balance} coins)"

    def save(self, *args, **kwargs):
        """Auto-create referral code if not exists - ENHANCED"""
        if not self.referral_code:
            # Use user's account number for referral code
            self.referral_code = f"TW{self.user.account_number}"
            print(f"🔑 Created referral code: {self.referral_code} for {self.user.email}")
        
        # Ensure we have a user before saving
        if not self.user_id:
            raise ValidationError("Affiliate must be associated with a user")
            
        super().save(*args, **kwargs)

    def award_referral_coins(self, coins=50):
        """Award coins to affiliate - ENHANCED WITH DEBUGGING"""
        try:
            print(f"💰 ATTEMPTING TO AWARD {coins} COINS TO {self.user.email}")
            print(f"📊 BEFORE - Balance: {self.coin_balance}, Total Earned: {self.total_coins_earned}")
            
            with transaction.atomic():
                self.total_coins_earned += coins
                self.coin_balance += coins
                self.save()
                
            print(f"✅ SUCCESS - New balance: {self.coin_balance}, Total earned: {self.total_coins_earned}")
            return True
            
        except Exception as e:
            print(f"❌ COIN AWARD ERROR for {self.user.email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def get_referral_link(self, request=None):
        """Get full referral link for sharing"""
        base_url = "https://www.tradewise-hub.com"
        if request:
            base_url = f"http://{request.get_host()}"
        return f"{base_url}/signup?ref={self.referral_code}"

    def get_referral_stats(self):
        """Get comprehensive referral statistics"""
        total_referrals = self.referrals.count()
        approved_referrals = self.referrals.filter(status='approved').count()
        pending_referrals = self.referrals.filter(status='pending').count()
        
        return {
            'total_referrals': total_referrals,
            'approved_referrals': approved_referrals,
            'pending_referrals': pending_referrals,
            'success_rate': (approved_referrals / total_referrals * 100) if total_referrals > 0 else 0,
            'total_coins_earned': self.total_coins_earned,
            'available_balance': self.coin_balance,
            'cash_value': self.coin_balance * 10,  # 10 Ksh per coin
        }

    def can_request_payout(self, coin_amount):
        """Check if affiliate can request payout"""
        return (
            self.coin_balance >= coin_amount and 
            coin_amount >= 50 and  # Minimum payout
            self.is_active
        )

    def request_payout(self, coin_amount, payment_method, **payment_details):
        """Request payout - reserves coins"""
        if not self.can_request_payout(coin_amount):
            return False, "Cannot process payout"
            
        try:
            with transaction.atomic():
                # Reserve coins by deducting from balance
                self.coin_balance -= coin_amount
                self.save()
                
                # Create payout request
                payout = PayoutRequest.objects.create(
                    user=self.user,
                    coin_amount=coin_amount,
                    payment_method=payment_method,
                    **payment_details
                )
                
                return True, payout
                
        except Exception as e:
            return False, str(e)

    class Meta:
        verbose_name = "Affiliate"
        verbose_name_plural = "Affiliates"
        ordering = ['-created_at']

class Referral(models.Model):
    """Referral tracking - COMPLETELY UPDATED FOR AUTO-APPROVAL"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='referrals')
    referred_user = models.ForeignKey(Tradeviewusers, on_delete=models.CASCADE, related_name='referred_by')
    coins_awarded = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status_display = self.get_status_display()
        return f"Referral: {self.referred_user.email} by {self.affiliate.user.email} ({status_display})"

    def save(self, *args, **kwargs):
        """Auto-approve new referrals and award coins"""
        is_new = self._state.adding  # Check if this is a new object
        
        if is_new and self.status == 'pending':
            # Auto-approve new referrals
            self.status = 'approved'
            self.coins_awarded = 50
            
        super().save(*args, **kwargs)
        
        # Award coins after saving
        if is_new and self.status == 'approved' and self.coins_awarded > 0:
            self.award_coins_to_affiliate()

    def award_coins_to_affiliate(self):
        """Award coins to affiliate - CALLED AUTOMATICALLY ON SAVE"""
        print(f"🔄 AWARDING {self.coins_awarded} COINS FOR REFERRAL {self.id}")
        
        try:
            with transaction.atomic():
                # Refresh affiliate data to ensure we have latest
                affiliate = Affiliate.objects.select_for_update().get(id=self.affiliate.id)
                
                # Update affiliate stats
                affiliate.total_referrals += 1
                affiliate.total_coins_earned += self.coins_awarded
                affiliate.coin_balance += self.coins_awarded
                affiliate.save()
                
                print(f"✅ COINS AWARDED: {self.coins_awarded} coins to {affiliate.user.email}")
                print(f"📊 NEW BALANCE: {affiliate.coin_balance} coins")
                print(f"👥 TOTAL REFERRALS: {affiliate.total_referrals}")
                
                # Send notification
                self.send_approval_notification()
                
        except Exception as e:
            print(f"❌ COIN AWARD ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    def approve_referral(self):
        """Approve referral and award coins - FOR MANUAL APPROVAL"""
        print(f"🔄 MANUAL APPROVAL FOR REFERRAL: {self.id}")
        
        if self.status != 'pending':
            print(f"⚠️ Referral {self.id} already processed - Status: {self.status}")
            return False
            
        try:
            with transaction.atomic():
                self.status = 'approved'
                self.coins_awarded = 50
                self.save()  # This will trigger award_coins_to_affiliate()
                
            return True
            
        except Exception as e:
            print(f"❌ MANUAL APPROVAL ERROR: {str(e)}")
            return False

    def reject_referral(self):
        """Reject referral without awarding coins"""
        if self.status == 'pending':
            self.status = 'rejected'
            self.coins_awarded = 0
            self.save()
            return True
        return False

    def send_approval_notification(self):
        """Send email notification to affiliate when referral is approved"""
        try:
            subject = '🎉 New Referral - 50 TWC Coins Awarded!'
            
            message = f"""
Referral Approved - TradeWise

Congratulations {self.affiliate.user.first_name}!

Someone signed up using your referral link:

👤 New User: {self.referred_user.first_name} {self.referred_user.second_name}
📧 Email: {self.referred_user.email}
🔢 TradeWise Number: {self.referred_user.account_number}

💰 You have been awarded {self.coins_awarded} TWC coins!

📊 Your Stats:
- New Balance: {self.affiliate.coin_balance} TWC coins
- Total Referrals: {self.affiliate.total_referrals}
- Total Coins Earned: {self.affiliate.total_coins_earned}

💸 Cash Value: KES {self.affiliate.coin_balance * 10}

You can redeem your coins anytime from your account dashboard.

Keep sharing your link to earn more coins! 🚀

Best regards,
TradeWise Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[self.affiliate.user.email],
                fail_silently=False,
            )
            print(f"📧 Referral approval notification sent to {self.affiliate.user.email}")
            return True
            
        except Exception as e:
            print(f"❌ Referral notification error: {str(e)}")
            return False

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
        unique_together = ('affiliate', 'referred_user')
        


class WeeklyNumber(models.Model):
    """Weekly TradeWise number - FIXED"""
    number = models.CharField(max_length=20, default="7 8 4 2 1")
    week_start = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Weekly Number: {self.number} ({self.week_start})"

    def save(self, *args, **kwargs):
        """Ensure only one active weekly number exists"""
        if self.is_active:
            # Deactivate all other weekly numbers
            WeeklyNumber.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current_number(cls):
        """Get current active weekly number"""
        return cls.objects.filter(is_active=True).first()

class PayoutRequest(models.Model):
    """Payout requests from affiliates - FIXED"""
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('paypal', 'PayPal'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]
    
    user = models.ForeignKey(Tradeviewusers, on_delete=models.CASCADE, related_name='payout_requests')
    coin_amount = models.PositiveIntegerField()
    amount_kes = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    mpesa_number = models.CharField(max_length=20, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account = models.CharField(max_length=50, blank=True, null=True)
    paypal_email = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout: {self.user.email} - KES {self.amount_kes}"

    def save(self, *args, **kwargs):
        """Auto-calculate KES amount (10 Ksh per coin)"""
        if self.coin_amount and not self.amount_kes:
            self.amount_kes = self.coin_amount * 10
        super().save(*args, **kwargs)

# ================== SYSTEM MODELS ==================

class Notification(models.Model):
    """System notifications"""
    user = models.ForeignKey(Tradeviewusers, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=50, default='info')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"

class AdminLog(models.Model):
    """Admin activity logging"""
    user = models.ForeignKey(Tradeviewusers, on_delete=models.SET_NULL, null=True, blank=True)  # Make it optional
    action = models.CharField(max_length=200)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        username = self.user.first_name if self.user else "System"
        return f"Admin Log: {username} - {self.action}"

# ================== SIMPLE PAYMENT MODEL ==================

class Payment(models.Model):
    """Simple payment model for basic functionality"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    plan_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.amount} - {self.status}"

class Transaction(models.Model):
    """Simple transaction model"""
    TRANSACTION_TYPES = [
        ('payment', 'Payment'),
        ('withdrawal', 'Withdrawal'),
        ('bonus', 'Bonus'),
    ]
    
    user = models.ForeignKey(Tradeviewusers, on_delete=models.CASCADE, null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"

# ================== SIGNALS ==================

@receiver(post_save, sender=Tradeviewusers)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when new user is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=Tradeviewusers)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()

# ================== TRADING SOFTWARE MODELS ==================

class SoftwareTool(models.Model):
    """Trading software, bots, and tools"""
    FILE_TYPES = [
        ('software', 'Trading Software'),
        ('indicator', 'Trading Indicator'), 
        ('bot', 'Trading Bot'),
        ('tool', 'Analysis Tool'),
        ('ebook', 'E-book/Guide'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='software')
    version = models.CharField(max_length=20, default='1.0')
    
    # File upload fields
    file = models.FileField(upload_to='software/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='software/thumbnails/', blank=True, null=True)
    
    # Software details
    compatibility = models.CharField(max_length=100, blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    installation_guide = models.TextField(blank=True, null=True)
    
    # Pricing and access
    is_free = models.BooleanField(default=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Stats
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    # Management
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    requires_vip = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Software Tool"
        verbose_name_plural = "Software Tools"
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_file_type_display()})"

    def save(self, *args, **kwargs):
        """Auto-activate all software when created"""
        if not self.pk:  # Only for new instances
            self.is_active = True
        super().save(*args, **kwargs)

    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
        self.save()

    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save()

# ================== AUTO-CREATE AFFILIATE PROFILES ==================

@receiver(post_save, sender=Tradeviewusers)
def create_affiliate_profile(sender, instance, created, **kwargs):
    """Automatically create affiliate profile for every new user"""
    if created:
        try:
            affiliate, created = Affiliate.objects.get_or_create(user=instance)
            if created:
                print(f"✅ AUTO-CREATED AFFILIATE: {instance.email} - Code: {affiliate.referral_code}")
            else:
                print(f"ℹ️ Affiliate already exists for: {instance.email}")
        except Exception as e:
            print(f"❌ AFFILIATE CREATION ERROR for {instance.email}: {str(e)}")

@receiver(post_save, sender=Tradeviewusers)
def save_affiliate_profile(sender, instance, **kwargs):
    """Save affiliate profile when user is saved"""
    try:
        if hasattr(instance, 'affiliate'):
            instance.affiliate.save()
    except Exception as e:
        print(f"❌ AFFILIATE SAVE ERROR: {str(e)}")        