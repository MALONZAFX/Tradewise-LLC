# myapp/models.py
from django.db import models
from django.template.loader import render_to_string
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
import uuid
import os
import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
import requests
import json

# ================== PAYSTACK PAYMENT SERVICE ==================

class PaystackService:
    """
    Paystack payment service integration
    """
    def __init__(self):
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        self.public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
        self.base_url = "https://api.paystack.co"
    
    def initialize_transaction(self, email, amount, reference, callback_url=None, metadata=None):
        """
        Initialize Paystack transaction
        """
        url = f"{self.base_url}/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo
            "reference": reference,
        }
        
        if callback_url:
            data["callback_url"] = callback_url
            
        if metadata:
            data["metadata"] = metadata
            
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            return response.json()
        except requests.exceptions.Timeout:
            return {"status": False, "message": "Request timeout"}
        except requests.exceptions.RequestException as e:
            return {"status": False, "message": str(e)}
        except Exception as e:
            return {"status": False, "message": str(e)}
    
    def verify_transaction(self, reference):
        """
        Verify Paystack transaction
        """
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

# ================== PAYMENT MODELS ==================

class PricingPlan(models.Model):
    """
    Pricing plans for trading packages with Paystack integration
    """
    PLAN_TYPES = [
        ('starter', 'Starter'),
        ('pro', 'Professional'),
        ('vip', 'VIP'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='custom')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    description = models.TextField()
    features = models.JSONField(default=list)
    is_highlighted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    duration_days = models.IntegerField(default=30, help_text="Plan duration in days")
    
    # Display settings
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
    
    def get_features_list(self):
        """Return features as a list"""
        return self.features if isinstance(self.features, list) else []
    
    def get_paystack_amount(self):
        """Get amount in kobo for Paystack"""
        return int(self.price * 100)
    
    def create_payment_transaction(self, email, user=None, ip_address=None, user_agent=None):
        """Create a new payment transaction for this plan"""
        reference = f"TRD{uuid.uuid4().hex[:12].upper()}"
        
        transaction = PaymentTransaction.objects.create(
            user=user,
            email=email,
            amount=self.price,
            plan=self,
            reference=reference,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return transaction

class PaymentTransaction(models.Model):
    """
    Track all payment transactions with Paystack integration
    """
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_ABANDONED = 'abandoned'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_ABANDONED, 'Abandoned'),
    ]
    
    # User information
    user = models.ForeignKey(
        'Tradeviewusers', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='payment_transactions'
    )
    email = models.EmailField(db_index=True)
    
    # Payment information
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    currency = models.CharField(max_length=3, default='KES')
    plan = models.ForeignKey(
        PricingPlan, 
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Paystack references
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    paystack_access_code = models.CharField(max_length=100, blank=True, null=True)
    paystack_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paystack_authorization_url = models.URLField(blank=True, null=True)
    
    # Status and timestamps
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default=STATUS_PENDING
    )
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for better tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Payment Transaction"
        verbose_name_plural = "Payment Transactions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.reference} - KES {self.amount} - {self.status}"
    
    def initialize_paystack_payment(self, request=None):
        """Initialize payment with Paystack"""
        paystack_service = PaystackService()
        
        # Build callback URL
        callback_url = None
        if request:
            callback_url = request.build_absolute_uri(f'/payment/verify/{self.reference}/')
        
        metadata = {
            'plan_id': self.plan.id,
            'plan_name': self.plan.name,
            'transaction_id': self.id,
            'custom_fields': [
                {
                    'display_name': "Plan",
                    'variable_name': "plan",
                    'value': self.plan.name
                },
                {
                    'display_name': "User Email", 
                    'variable_name': "user_email",
                    'value': self.email
                }
            ]
        }
        
        response = paystack_service.initialize_transaction(
            email=self.email,
            amount=self.amount,
            reference=self.reference,
            callback_url=callback_url,
            metadata=metadata
        )
        
        if response.get('status'):
            self.paystack_access_code = response['data']['access_code']
            self.paystack_authorization_url = response['data']['authorization_url']
            self.metadata['paystack_response'] = response
            self.save()
            return True, response
        else:
            self.status = self.STATUS_FAILED
            self.metadata['paystack_error'] = response
            self.save()
            return False, response
    
    def verify_paystack_payment(self):
        """Verify payment status with Paystack"""
        paystack_service = PaystackService()
        response = paystack_service.verify_transaction(self.reference)
        
        if response.get('status') and response['data']['status'] == 'success':
            return self.mark_as_successful(response['data'])
        else:
            return self.mark_as_failed(response.get('message', 'Payment verification failed'))
    
    def mark_as_successful(self, paystack_data=None):
        """Mark transaction as successful"""
        self.status = self.STATUS_SUCCESS
        self.paystack_transaction_id = paystack_data.get('id') if paystack_data else None
        self.payment_date = timezone.now()
        
        if paystack_data:
            self.metadata['paystack_verification'] = paystack_data
        
        self.save()
        
        # Update user plan
        if self.user:
            self.user.plan = self.plan.name
            self.user.save()
        
        return True
    
    def mark_as_failed(self, reason=None):
        """Mark transaction as failed"""
        self.status = self.STATUS_FAILED
        self.metadata['failure_reason'] = reason or "Payment failed"
        self.save()
        return False
    
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == self.STATUS_SUCCESS
    
    def get_payment_url(self):
        """Get Paystack payment URL"""
        return self.paystack_authorization_url

class PaymentWebhookLog(models.Model):
    """
    Log Paystack webhook calls for debugging and security
    """
    EVENT_TYPES = [
        ('charge.success', 'Charge Success'),
        ('charge.failure', 'Charge Failure'),
        ('transfer.success', 'Transfer Success'),
        ('transfer.failure', 'Transfer Failure'),
    ]
    
    event_type = models.CharField(max_length=100, choices=EVENT_TYPES)
    reference = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField()
    headers = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    
    # Processing status
    status = models.CharField(max_length=20, default='received')
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    # Relations
    transaction = models.ForeignKey(
        PaymentTransaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='webhook_logs'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Payment Webhook Log"
        verbose_name_plural = "Payment Webhook Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.reference} - {self.status}"

# ================== USER MODELS ==================

class Tradeviewusers(models.Model):
    first_name = models.CharField(max_length=50)
    second_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    
    is_active = models.BooleanField(default=True)
    
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
            
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def send_verification_email(self):
        """Send email verification with FAST performance"""
        if not self.email_verification_token:
            return False
            
        subject = '✅ Verify Your TradeWise Account'
        verification_url = f"{getattr(settings, 'SITE_URL', 'https://www.tradewise-hub.com/')}/verify-email/{self.email_verification_token}/"
        
        # Render BEAUTIFUL HTML template
        html_message = render_to_string('emails/verification_email.html', {
            'user': self,
            'verification_url': verification_url,
        })
        
        plain_message = f"""
Dear {self.first_name},

Welcome to TradeWise! Please verify your email address to activate your account.

Your Account Details:
- Name: {self.first_name} {self.second_name}
- TradeWise Number: {self.account_number}
- Email: {self.email}

Click the link below to verify your email:
{verification_url}

If you didn't create this account, please ignore this email.

Best regards,
TradeWise Team
        """
        
        try:
            # FAST EMAIL SENDING - KEEP ORIGINAL APPROACH
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[self.email],
                html_message=html_message,  # ✅ BEAUTIFUL TEMPLATE
                fail_silently=False,
            )
            print(f"✅ FAST: Verification email sent to: {self.email}")
            return True
            
        except Exception as e:
            print(f"❌ Email error for {self.email}: {str(e)}")
            return False

    def send_password_reset_email(self):
        """Send password reset email with FAST performance"""
        try:
            self.password_reset_token = secrets.token_urlsafe(32)
            self.save()
            
            subject = '🔒 Reset Your TradeWise Password'
            reset_url = f"{getattr(settings, 'SITE_URL', 'https://www.tradewise-hub.com/')}/reset-password/{self.password_reset_token}/"
            
            # Render BEAUTIFUL HTML template
            html_message = render_to_string('emails/password_reset.html', {
                'user': self,
                'reset_url': reset_url,
                'request_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
            
            plain_message = f"""
Dear {self.first_name},

You requested to reset your password for your TradeWise account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this reset, please ignore this email.

Best regards,
TradeWise Team
            """
            
            # FAST EMAIL SENDING
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[self.email],
                html_message=html_message,  # ✅ BEAUTIFUL TEMPLATE
                fail_silently=False,
            )
            print(f"✅ FAST: Password reset email sent to: {self.email}")
            return True
            
        except Exception as e:
            print(f"❌ Password reset email error for {self.email}: {str(e)}")
            return False

    def send_welcome_email(self, plain_password):
        """Send welcome email with FAST performance"""
        try:
            subject = '🎉 Welcome to TradeWise - Your Account is Ready!'
            
            # Render BEAUTIFUL HTML template
            html_message = render_to_string('emails/welcome_email.html', {
                'user': self,
                'plain_password': plain_password,
            })
            
            plain_message = f"""
Dear {self.first_name} {self.second_name},

Welcome to TradeWise! Your account has been created successfully.

Your Account Details:
- TradeWise Number: {self.account_number}
- Name: {self.first_name} {self.second_name}
- Email: {self.email}
- Password: {plain_password}

Please keep this information secure.

You can access your account here: {getattr(settings, 'SITE_URL', 'https://www.tradewise-hub.com/')}/loginpage/

Best regards,
TradeWise Team
            """
            
            # FAST EMAIL SENDING
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[self.email],
                html_message=html_message,  # ✅ BEAUTIFUL TEMPLATE
                fail_silently=False,
            )
            print(f"✅ FAST: Welcome email sent to: {self.email}")
            return True
            
        except Exception as e:
            print(f"❌ Welcome email error for {self.email}: {str(e)}")
            return False

    def send_order_confirmation_email(self, order_details):
        """Send order confirmation email with FAST performance"""
        try:
            subject = '✅ Order Confirmation - TradeWise'
            
            # Render BEAUTIFUL HTML template
            html_message = render_to_string('emails/order_confirmation.html', {
                'user': self,
                'order_details': order_details,
                'order_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
            
            plain_message = f"""
Dear {self.first_name},

Thank you for your order with TradeWise!

Order Details:
- Order ID: {order_details.get('order_id', 'N/A')}
- Service: {order_details.get('service', 'N/A')}
- Amount: {order_details.get('amount', 'N/A')}
- Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

We will process your order shortly and contact you if needed.

Best regards,
TradeWise Team
            """
            
            # FAST EMAIL SENDING
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[self.email],
                html_message=html_message,  # ✅ BEAUTIFUL TEMPLATE
                fail_silently=False,
            )
            print(f"✅ FAST: Order confirmation sent to: {self.email}")
            return True
            
        except Exception as e:
            print(f"❌ Order confirmation email error: {str(e)}")
            return False

    def send_new_user_notification(self):
        """Send FAST notification to admin about new user registration"""
        try:
            subject = '👤 New User Registration - TradeWise'
            
            # Render BEAUTIFUL HTML template for admin
            html_message = render_to_string('emails/new_user.html', {
                'user': self,
                'registration_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'site_url': getattr(settings, 'SITE_URL', 'https://www.tradewise-hub.com/'),
            })
            
            plain_message = f"""
New User Registration on TradeWise

User Details:
- Name: {self.first_name} {self.second_name}
- Email: {self.email}
- TradeWise Number: {self.account_number}
- Phone: {self.phone or 'Not provided'}
- Registration Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

You can view this user in the admin dashboard.

Best regards,
TradeWise System
            """
            
            admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
            
            # FAST EMAIL SENDING
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[admin_email],
                html_message=html_message,  # ✅ BEAUTIFUL TEMPLATE
                fail_silently=False,
            )
            print(f"✅ FAST: New user notification sent for: {self.email}")
            return True
            
        except Exception as e:
            print(f"❌ New user notification email error: {str(e)}")
            return False

    def __str__(self):
        return f"{self.first_name} {self.second_name} (TWN: {self.account_number})"

    class Meta:
        verbose_name = "TradeView User"
        verbose_name_plural = "TradeView Users"

# ================== CAPITAL & PAYMENT MODELS ==================

class CapitalAccess(models.Model):
    user = models.OneToOneField(Tradeviewusers, on_delete=models.CASCADE, related_name='capital_access')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Capital Access for {self.user.email} (Balance: {self.balance})"

    class Meta:
        verbose_name = "Capital Access"
        verbose_name_plural = "Capital Access"

class ClassesPayment(models.Model):
    STATUS_CHOICES = [
        ('initialized', 'Initialized'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    phone = models.CharField(max_length=15)
    amount = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    package = models.CharField(max_length=15)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='initialized')

    def __str__(self):
        return f"{self.phone} - {self.package} ({self.status})"

    class Meta:
        verbose_name = "Classes Payment"
        verbose_name_plural = "Classes Payments"

class MerchPayment(models.Model):
    STATUS_CHOICES = [
        ('initialized', 'Initialized'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    phone = models.CharField(max_length=15)
    amount = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    merchid = models.CharField(max_length=15)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='initialized')

    def __str__(self):
        return f"{self.phone} - {self.merchid} ({self.status})"

    class Meta:
        verbose_name = "Merchandise Payment"
        verbose_name_plural = "Merchandise Payments"

# ================== TRADING & SERVICE MODELS ==================

class ForexAnalysis(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='forex_analysis/images/', blank=True, null=True)
    video = models.FileField(upload_to='forex_analysis/videos/', blank=True, null=True)
    analysis_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Forex Analysis"
        verbose_name_plural = "Forex Analyses"
        ordering = ['-created_at']

class Merchandise(models.Model):
    CATEGORY_CHOICES = [
        ('caps-hats', 'Caps & Hats'),
        ('hoodies', 'Hoodies'),
        ('t-shirts', 'T-Shirts'),
        ('accessories', 'Accessories'),
    ]

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='merchandise/images/')
    description = models.TextField()
    price = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Merchandise"
        verbose_name_plural = "Merchandise"
        ordering = ['-created_at']

class Coaching(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Coaching Program"
        verbose_name_plural = "Coaching Programs"
        ordering = ['-created_at']

class Request(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('completed', 'Completed')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "General Request"
        verbose_name_plural = "General Requests"
        ordering = ['-created_at']

class ConsultationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    class_interest = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.class_interest}"

    class Meta:
        verbose_name = "Consultation Request"
        verbose_name_plural = "Consultation Requests"
        ordering = ['-created_at']

class CoachingRequest(models.Model):
    CLASS_TYPES = [
        ('physical', 'Physical Coaching'),
        ('online', 'Online Coaching'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    class_type = models.CharField(max_length=20, choices=CLASS_TYPES)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.get_class_type_display()}"

    class Meta:
        verbose_name = "Coaching Request"
        verbose_name_plural = "Coaching Requests"
        ordering = ['-created_at']

class Strategy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='strategies/', blank=True, null=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stats = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Trading Strategy"
        verbose_name_plural = "Trading Strategies"
        ordering = ['-created_at']

class Signal(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='signals/', blank=True, null=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    accuracy_forex = models.PositiveSmallIntegerField(default=80)
    accuracy_crypto = models.PositiveSmallIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Trading Signal"
        verbose_name_plural = "Trading Signals"
        ordering = ['-created_at']

class MarketServiceRequest(models.Model):
    SERVICE_CHOICES = [
        ('Strategy', 'Strategy'),
        ('Signal', 'Signal'),
    ]
    
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    selected_service = models.CharField(max_length=200)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('completed', 'Completed')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.service_type} - {self.selected_service}"

    class Meta:
        verbose_name = "Market Service Request"
        verbose_name_plural = "Market Service Requests"
        ordering = ['-created_at']

class GeneralServiceRequest(models.Model):
    SERVICE_TYPES = [
        ('Strategy', 'Strategy'),
        ('Signal', 'Signal'),
        ('Chart Lab', 'Chart Lab'),
        ('Copy Trading', 'Copy Trading'),
        ('Live Trading', 'Live Trading'),
        ('Mentorship', 'Mentorship'),
        ('Market Analysis', 'Market Analysis'),
        ('Other', 'Other'),
    ]
    
    EXPERIENCE_LEVELS = [
        ('beginner', 'Beginner (0-6 months)'),
        ('intermediate', 'Intermediate (6 months - 2 years)'),
        ('advanced', 'Advanced (2+ years)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    selected_service = models.CharField(max_length=100)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, blank=True, null=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.service_type} - {self.selected_service}"

    class Meta:
        verbose_name = "General Service Request"
        verbose_name_plural = "General Service Requests"
        ordering = ['-created_at']

class TradingService(models.Model):
    CATEGORY_CHOICES = [
        ('copytrading', 'Copy Trading'),
        ('livetrading', 'Live Trading'),
        ('signals', 'Signal Service'),
        ('mentorship', 'Mentorship'),
        ('analysis', 'Market Analysis'),
        ('others', 'Other Services'),
    ]

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    price_label = models.CharField(max_length=100)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='others')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

    class Meta:
        verbose_name = "Trading Service"
        verbose_name_plural = "Trading Services"
        ordering = ['-created_at']

class ServiceRevenue(models.Model):
    SERVICE_CHOICES = [
        ('Strategy - Custom Strategy Development', 'Strategy - Custom Strategy Development'),
        ('Strategy - Premium Mentorship', 'Strategy - Premium Mentorship'),
        ('Signal - Premium Signal Service', 'Signal - Premium Signal Service'),
        ('Signal - Basic Signals', 'Signal - Basic Signals'),
        ('Chart Lab', 'Chart Lab'),
        ('Copy Trading', 'Copy Trading'),
        ('Live Trading', 'Live Trading'),
        ('Mentorship', 'Mentorship'),
        ('Market Analysis', 'Market Analysis'),
        ('Other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    service_type = models.CharField(max_length=100, choices=SERVICE_CHOICES)
    client_name = models.CharField(max_length=200)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client_name} - {self.service_type} - ${self.amount}"

    def clean(self):
        if self.amount and self.amount < 0:
            raise ValidationError({'amount': 'Amount cannot be negative.'})

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Service Revenue"
        verbose_name_plural = "Service Revenues"

class Software(models.Model):
    FILE_TYPES = [
        ('software', 'Software'),
        ('ebook', 'E-Book'),
        ('indicator', 'Trading Indicator'),
        ('template', 'Template'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    version = models.CharField(max_length=20)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file = models.FileField(upload_to='software/')
    thumbnail = models.ImageField(upload_to='software/thumbnails/', null=True, blank=True)
    download_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} v{self.version}"

    class Meta:
        verbose_name = "Software"
        verbose_name_plural = "Software"
        ordering = ['-created_at']

# ================== ADMIN & LOGGING MODELS ==================

class AdminLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('view', 'View'),
        ('export', 'Export'),
        ('user_disabled', 'User Disabled'),
        ('user_enabled', 'User Enabled'),
        ('password_reset_sent', 'Password Reset Sent'),
        ('system', 'System Action'),
    ]
    
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Admin Log"
        verbose_name_plural = "Admin Logs"

    def __str__(self):
        return f"{self.admin_user.username} - {self.action} - {self.timestamp}"

    def get_action_display(self):
        """Enhanced action display for admin dashboard"""
        action_map = {
            'create': 'Created',
            'update': 'Updated',
            'delete': 'Deleted',
            'login': 'Logged In',
            'logout': 'Logged Out',
            'approve': 'Approved',
            'reject': 'Rejected',
            'view': 'Viewed',
            'export': 'Exported',
            'user_disabled': 'Disabled User',
            'user_enabled': 'Enabled User',
            'password_reset_sent': 'Sent Password Reset',
            'system': 'System Action'
        }
        return action_map.get(self.action, self.action.title())

# ================== AFFILIATE & COIN MODELS ==================

class TradeWiseCoin(models.Model):
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('TRANSFER', 'Transfer'),
        ('EARN', 'Earn'),
    ]
    
    user = models.ForeignKey(Tradeviewusers, on_delete=models.CASCADE, related_name='coins', null=True, blank=True)
    
    # ✅ FIXED: Added missing coin_symbol field
    coin_symbol = models.CharField(max_length=10, default='TWC')
    coin_name = models.CharField(max_length=100, default='TradeWise Coin')
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='BUY')
    quantity = models.DecimalField(max_digits=15, decimal_places=8, default=1000.00000000)
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0.10)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.coin_symbol} - {self.transaction_type} - {self.quantity}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "TradeWise Coin"
        verbose_name_plural = "TradeWise Coins"

class Affiliate(models.Model):
    user = models.OneToOneField('Tradeviewusers', on_delete=models.CASCADE, related_name='affiliate')
    referral_code = models.CharField(max_length=20, unique=True)
    total_referrals = models.IntegerField(default=0)
    total_coins_earned = models.IntegerField(default=0)
    coin_balance = models.IntegerField(default=0)
    total_payouts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.second_name} - {self.referral_code}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        code = str(uuid.uuid4())[:8].upper()
        while Affiliate.objects.filter(referral_code=code).exists():
            code = str(uuid.uuid4())[:8].upper()
        return code

    @property
    def pending_payouts(self):
        return self.user.payout_requests.filter(status='pending').aggregate(Sum('amount_kes'))['amount_kes__sum'] or 0

    @property
    def completed_payouts(self):
        return self.user.payout_requests.filter(status='approved').aggregate(Sum('amount_kes'))['amount_kes__sum'] or 0

    @property
    def referral_link(self):
        return f"https://www.tradewise-hub.com/signup?ref={self.referral_code}"

    class Meta:
        verbose_name = "Affiliate"
        verbose_name_plural = "Affiliates"

class Referral(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    referrer = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='referrals')
    referred_user = models.ForeignKey('Tradeviewusers', on_delete=models.CASCADE, related_name='referred_by')
    coins_earned = models.IntegerField(default=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.referrer.user.email} -> {self.referred_user.email}"

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = Referral.objects.get(pk=self.pk)
                if old_instance.status != 'approved' and self.status == 'approved':
                    self.award_coins()
            except Referral.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        if not self.pk and self.status == 'approved':
            self.award_coins()

    def award_coins(self):
        try:
            affiliate = self.referrer
            affiliate.total_coins_earned += self.coins_earned
            affiliate.coin_balance += self.coins_earned
            affiliate.total_referrals += 1
            affiliate.save()
            
            print(f"✅ Awarded {self.coins_earned} coins to {affiliate.user.email} for referral {self.referred_user.email}")
            
        except Exception as e:
            print(f"❌ Error awarding coins: {e}")

    class Meta:
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
        unique_together = ['referrer', 'referred_user']

class PayoutRequest(models.Model):
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

    user = models.ForeignKey('Tradeviewusers', on_delete=models.CASCADE, related_name='payout_requests')
    coin_amount = models.IntegerField()
    amount_kes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    
    mpesa_number = models.CharField(max_length=20, blank=True, null=True)
    bank_account = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    paypal_email = models.EmailField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payouts')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout #{self.id} - {self.user.first_name} {self.user.second_name} - {self.amount_kes} KES"

    def save(self, *args, **kwargs):
        if self.coin_amount and not self.amount_kes:
            self.amount_kes = self.coin_amount * 10
        
        super().save(*args, **kwargs)

    @property
    def payment_details_display(self):
        if self.payment_method == 'mpesa':
            return f"M-Pesa: {self.mpesa_number}"
        elif self.payment_method == 'bank':
            return f"Bank: {self.bank_name} - {self.bank_account}"
        elif self.payment_method == 'paypal':
            return f"PayPal: {self.paypal_email}"
        return "No payment details"

    class Meta:
        verbose_name = "Payout Request"
        verbose_name_plural = "Payout Requests"
        ordering = ['-created_at']

class WeeklyNumber(models.Model):
    number = models.CharField(max_length=20)
    week_start = models.DateField()
    week_end = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Weekly Number: {self.number} ({self.week_start} to {self.week_end})"

    def save(self, *args, **kwargs):
        if self.is_active:
            WeeklyNumber.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        if self.week_start and not self.week_end:
            self.week_end = self.week_start + timezone.timedelta(days=6)
            
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-week_start']
        verbose_name = "Weekly Number"
        verbose_name_plural = "Weekly Numbers"

class AffiliateBonus(models.Model):
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name='bonuses')
    weekly_number = models.ForeignKey(WeeklyNumber, on_delete=models.CASCADE, related_name='bonuses')
    bonus_coins = models.IntegerField(default=100)
    is_claimed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bonus for {self.affiliate.user.email} - {self.bonus_coins} coins"

    class Meta:
        verbose_name_plural = "Affiliate Bonuses"
        unique_together = ['affiliate', 'weekly_number']
        verbose_name = "Affiliate Bonus"

# ================== USER PROFILE & NOTIFICATION MODELS ==================

class UserProfile(models.Model):
    user = models.OneToOneField(Tradeviewusers, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    trading_experience = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], default='beginner')
    preferred_language = models.CharField(max_length=10, default='en')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.first_name} {self.user.second_name}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('payment', 'Payment'),
        ('referral', 'Referral'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(Tradeviewusers, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

# ================== TRADEWISE CARD MODEL ==================

class TradeWiseCard(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]
    
    # ✅ REQUIRED FIELDS FOR FRONTEND DISPLAY
    card_number = models.CharField(max_length=16, default='6734 559')
    capital_available = models.CharField(max_length=50, default='$500,000')
    partner_name = models.CharField(max_length=100, default='SPALIS FX')
    contact_number = models.CharField(max_length=20, default='+254742962615')
    
    # ✅ FIXED: Make user field optional for system cards
    user = models.ForeignKey(Tradeviewusers, on_delete=models.CASCADE, related_name='cards', null=True, blank=True)
    
    # ✅ FIXED: Added missing card_holder_name field
    card_holder_name = models.CharField(max_length=100, blank=True, default='TradeWise Holder')
    
    expiry_date = models.DateField(null=True, blank=True)
    cvv = models.CharField(max_length=3, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    # Optional admin fields
    title = models.CharField(max_length=200, default='TradeWise Premium')
    subtitle = models.CharField(max_length=200, blank=True)
    description = models.TextField(default='Access premium trading features and exclusive content')
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=49.99)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=499.99)
    image = models.ImageField(upload_to='tradewise_cards/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Card {self.card_number} - {self.user.email}"
        return f"System Card {self.card_number} - {self.partner_name}"

    class Meta:
        verbose_name = "TradeWise Card"
        verbose_name_plural = "TradeWise Cards"
        ordering = ['-created_at']

# ================== ADDITIONAL SERVICE MODELS ==================

class TradingClass(models.Model):
    CLASS_TYPES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('professional', 'Professional'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    class_type = models.CharField(max_length=20, choices=CLASS_TYPES, default='beginner')
    duration = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='trading_classes/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_class_type_display()})"

    class Meta:
        verbose_name = "Trading Class"
        verbose_name_plural = "Trading Classes"
        ordering = ['-created_at']

class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('trading', 'Trading'),
        ('affiliate', 'Affiliate Program'),
        ('payment', 'Payment'),
        ('technical', 'Technical Support'),
    ]
    
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question

    class Meta:
        ordering = ['category', 'order']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"
        ordering = ['-subscribed_at']

# ================== BLOG & TESTIMONIAL MODELS ==================

class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    
    # ✅ FIXED: Added missing excerpt field
    excerpt = models.TextField(blank=True, default='')
    
    image = models.ImageField(upload_to='blog/images/', blank=True, null=True)
    author = models.CharField(max_length=100, default='Admin')
    is_published = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ['-created_at']

class Testimonial(models.Model):
    ROLE_CHOICES = [
        ('Beginner Trader', 'Beginner Trader'),
        ('Intermediate Trader', 'Intermediate Trader'), 
        ('Advanced Trader', 'Advanced Trader'),
        ('Professional Trader', 'Professional Trader'),
        ('Forex Trader', 'Forex Trader'),
        ('Crypto Trader', 'Crypto Trader'),
        ('Funded Trader', 'Funded Trader'),
        ('Student', 'Student'),
        ('Client', 'Client'),
        ('Trader', 'Trader'),  # Default fallback
    ]
    
    # ✅ FIXED: Added missing author_name field
    author_name = models.CharField(max_length=100, default='Anonymous')
    email = models.EmailField(blank=True, null=True)
    user_role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Trader')
    rating = models.IntegerField(
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')],
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    content = models.TextField()
    
    # Optional fields
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    
    # Status fields - THESE ARE CRITICAL FOR YOUR VIEWS TO WORK
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    from_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Testimonial by {self.author_name} ({self.rating}★)"

    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"

    def get_rating_stars(self):
        """Return stars for display"""
        return '★' * self.rating + '☆' * (5 - self.rating)

# ================== SIGNALS ==================

@receiver(post_save, sender=Tradeviewusers)
def setup_new_user(sender, instance, created, **kwargs):
    """
    Combined signal to setup all user-related records in one transaction
    """
    if created:
        try:
            with transaction.atomic():
                # 1. Create CapitalAccess
                capital_access, ca_created = CapitalAccess.objects.get_or_create(
                    user=instance,
                    defaults={'balance': 0.00, 'currency': 'USD', 'status': 'active'}
                )
                
                # 2. Create Affiliate profile
                affiliate, aff_created = Affiliate.objects.get_or_create(
                    user=instance,
                    defaults={'referral_code': Affiliate.generate_referral_code()}
                )
                
                # 3. Create UserProfile
                profile, prof_created = UserProfile.objects.get_or_create(
                    user=instance,
                    defaults={'trading_experience': 'beginner', 'profile_completed': False}
                )
                
                print(f"✅ User setup complete for: {instance.email}")
                print(f"   - CapitalAccess: {'Created' if ca_created else 'Exists'}")
                print(f"   - Affiliate: {'Created' if aff_created else 'Exists'}")
                print(f"   - UserProfile: {'Created' if prof_created else 'Exists'}")
                
        except Exception as e:
            print(f"❌ Comprehensive user setup failed for {instance.email}: {e}")
            import traceback
            traceback.print_exc()

@receiver(post_save, sender=Referral)
def handle_referral_status_change(sender, instance, created, **kwargs):
    """Handle referral status changes and award coins"""
    if not created and instance.status == 'approved':
        print(f"🔄 Referral status changed to approved for {instance}")

@receiver(post_save, sender=TradeWiseCard)
def ensure_system_card_exists(sender, instance, created, **kwargs):
    """Ensure at least one system card exists for the frontend"""
    if created and not instance.user:
        print(f"✅ Created system TradeWise card: {instance.card_number}")

# ================== UTILITY FUNCTIONS ==================

def create_default_plans():
    """
    Create default pricing plans for Paystack integration
    """
    plans_data = [
        {
            'name': 'Starter Package',
            'plan_type': 'starter',
            'price': 5999.00,
            'description': 'Perfect for beginners starting their trading journey',
            'features': [
                '3 daily trade signals',
                'Email alerts',
                'Basic trading guides', 
                'Community access',
                'Mobile notifications',
                'Basic support'
            ],
            'is_highlighted': False,
            'duration_days': 30,
            'display_order': 1,
            'color_scheme': '#0056b3'
        },
        {
            'name': 'Pro Trader',
            'plan_type': 'pro',
            'price': 12999.00,
            'description': 'For serious traders looking to maximize profits',
            'features': [
                '8 daily trade signals',
                'SMS/WhatsApp alerts',
                'Weekly training videos',
                'Advanced analytics',
                'Priority support',
                'Copy trading access'
            ],
            'is_highlighted': True,
            'duration_days': 30,
            'display_order': 2,
            'color_scheme': '#28a745'
        },
        {
            'name': 'VIP Elite', 
            'plan_type': 'vip',
            'price': 24999.00,
            'description': 'Ultimate trading experience with personalized mentorship',
            'features': [
                'Unlimited signals',
                '1-on-1 mentor sessions',
                'Live trading rooms', 
                'Capital funding access',
                'Risk management plans',
                '24/7 direct support'
            ],
            'is_highlighted': False,
            'duration_days': 30,
            'display_order': 3,
            'color_scheme': '#dc3545'
        }
    ]
    
    for plan_data in plans_data:
        plan, created = PricingPlan.objects.get_or_create(
            name=plan_data['name'],
            defaults=plan_data
        )
        if created:
            print(f"✅ Created plan: {plan.name}")
        else:
            print(f"📋 Plan already exists: {plan.name}")

def get_admin_stats():
    """Get real-time admin dashboard statistics"""
    try:
        total_users = Tradeviewusers.objects.count()
        new_users_today = Tradeviewusers.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        total_revenue = ServiceRevenue.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        pending_requests = (
            ConsultationRequest.objects.filter(status='pending').count() +
            CoachingRequest.objects.filter(status='pending').count() +
            GeneralServiceRequest.objects.filter(status='pending').count()
        )
        
        active_traders = Tradeviewusers.objects.filter(is_active=True).count()
        
        return {
            'total_users': total_users,
            'new_users_today': new_users_today,
            'total_revenue': float(total_revenue),
            'pending_requests': pending_requests,
            'active_traders': active_traders,
        }
    except Exception as e:
        print(f"❌ Error getting admin stats: {e}")
        return {
            'total_users': 0,
            'new_users_today': 0,
            'total_revenue': 0,
            'pending_requests': 0,
            'active_traders': 0,
        }

def get_recent_admin_activity(limit=10):
    """Get recent admin activity for dashboard"""
    try:
        return AdminLog.objects.all().order_by('-timestamp')[:limit]
    except Exception as e:
        print(f"❌ Error getting admin activity: {e}")
        return []

def create_admin_log_entry(admin_user, action, model_name, description, object_id=None, request=None):
    """Utility function to create admin log entries"""
    try:
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
        
        AdminLog.objects.create(
            admin_user=admin_user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            description=description,
            ip_address=ip_address
        )
        return True
    except Exception as e:
        print(f"❌ Error creating admin log: {e}")
        return False

def create_default_data():
    """Create default system data"""
    # Create a default TradeWise card if none exists
    if not TradeWiseCard.objects.exists():
        TradeWiseCard.objects.create(
            card_number='6734 559',
            capital_available='$500,000',
            partner_name='SPALIS FX',
            contact_number='+254742962615',
            card_holder_name='TradeWise System',
            status='active'
        )
        print("✅ Created default TradeWise card")
    
    # Create default pricing plans
    create_default_plans()
    
    print("✅ Default data setup complete")

# Initialize default data when models are loaded
#create_default_data()