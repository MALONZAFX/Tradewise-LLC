# myapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db.models import Q, Sum, Avg, Count
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
import uuid
import random
import json
from .models import PricingPlan, PaymentTransaction, BlogPost
import json
from .models import (
    Tradeviewusers,
    CapitalAccess,
    ClassesPayment,
    MerchPayment,
    ForexAnalysis,
    Merchandise,
    Coaching,
    Request,
    ConsultationRequest,
    CoachingRequest,
    Strategy,
    Signal,
    MarketServiceRequest,
    GeneralServiceRequest,
    TradingService,
    TradeWiseCoin,
    ServiceRevenue,
    TradeWiseCard,
    TradingClass,
    FAQ,
    Testimonial,
    NewsletterSubscriber,
    Software,
    # AFFILIATE MODELS
    Affiliate,
    Referral,
    PayoutRequest,
    WeeklyNumber,
    AffiliateBonus,
    # ADDITIONAL MODELS
    UserProfile,
    Notification,
    AdminLog,
    BlogPost
)
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.mail import send_mail
import requests
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

# ADMIN IMPORTS
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
import json
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# PASSWORD SECURITY
from django.contrib.auth.hashers import make_password, check_password
import secrets

# ADD THESE NEW IMPORTS FOR USER MANAGEMENT
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse

# AJAX VIEWS IMPORTS
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# STATIC FILES
from django.templatetags.static import static

# SLUGIFY FOR BLOG
from django.utils.text import slugify


# ================== PAYSTACK SERVICE CLASS ==================

class PaystackService:
    """Paystack payment service integration - ADDED DIRECTLY TO VIEWS.PY"""
    
    def __init__(self):
        self.secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', '')
        self.public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
        self.base_url = "https://api.paystack.co"
    
    def _make_request(self, method, endpoint, data=None):
        """Make API request to Paystack"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                return {'status': False, 'message': 'Invalid HTTP method'}
            
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'status': False, 'message': str(e)}
    
    def initialize_transaction(self, email, amount, reference, callback_url=None, metadata=None):
        """Initialize a transaction"""
        endpoint = "/transaction/initialize"
        data = {
            'email': email,
            'amount': int(amount * 100),  # Convert to kobo
            'reference': reference,
            'callback_url': callback_url,
            'metadata': metadata or {}
        }
        
        return self._make_request('POST', endpoint, data)
    
    def verify_transaction(self, reference):
        """Verify a transaction"""
        endpoint = f"/transaction/verify/{reference}"
        return self._make_request('GET', endpoint)
    
    def create_plan(self, name, amount, interval='monthly'):
        """Create a subscription plan"""
        endpoint = "/plan"
        data = {
            'name': name,
            'amount': int(amount * 100),
            'interval': interval,
            'currency': 'NGN'
        }
        return self._make_request('POST', endpoint, data)
    
    def create_customer(self, email, first_name=None, last_name=None, phone=None):
        """Create a customer"""
        endpoint = "/customer"
        data = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone
        }
        return self._make_request('POST', endpoint, data)
    
    def charge_authorization(self, email, amount, authorization_code, reference):
        """Charge a customer using authorization code"""
        endpoint = "/transaction/charge_authorization"
        data = {
            'email': email,
            'amount': int(amount * 100),
            'authorization_code': authorization_code,
            'reference': reference
        }
        return self._make_request('POST', endpoint, data)


# ================== UTILITY FUNCTIONS SECTION ==================

def is_admin_user(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def get_client_ip(request):
    """Get client IP address for logging"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_admin_log(admin_user, action, model_name, description, object_id=None, request=None):
    """Safely create admin log entry"""
    try:
        ip_address = get_client_ip(request) if request else None
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
        print(f"⚠️ AdminLog creation failed: {e}")
        return False



# ================= EXPLORE====================        
def explore(request):
    return render(request, 'explore.html')


# ================== SAFE HELPER FUNCTIONS SECTION ==================

def get_or_create_tradewise_coin():
    """Get or create TradeWiseCoin"""
    try:
        coin = TradeWiseCoin.objects.first()
        if not coin:
            default_user = Tradeviewusers.objects.first()
            if default_user:
                coin = TradeWiseCoin.objects.create(
                    user=default_user,
                    coin_symbol='TWC',
                    coin_name='TradeWise Coin',
                    transaction_type='BUY',
                    quantity=1000.00000000,
                    price=0.10,
                    notes='Initial TradeWise Coin creation'
                )
            else:
                # Create minimal default user if none exists
                default_user = Tradeviewusers.objects.create(
                    first_name='System',
                    second_name='Admin',
                    email='system@trade-wise.co.ke',
                    password='temp_password123'
                )
                coin = TradeWiseCoin.objects.create(
                    user=default_user,
                    coin_symbol='TWC',
                    coin_name='TradeWise Coin',
                    transaction_type='BUY',
                    quantity=1000.00000000,
                    price=0.10,
                    notes='Initial TradeWise Coin creation'
                )
        return coin
    except Exception as e:
        print(f"⚠️ Error in get_or_create_tradewise_coin: {e}")
        # Return mock object if database error
        class MockCoin:
            coin_symbol = 'TWC'
            coin_name = 'TradeWise Coin'
            transaction_type = 'BUY'
            quantity = 1000.00000000
            price = 0.10
            notes = 'Initial TradeWise Coin creation'
            
            def save(self):
                pass
        return MockCoin()

def get_or_create_tradewise_card():
    """Get or create TradeWiseCard - FIXED VERSION"""
    try:
        # First try to get a system card (no user assigned)
        card = TradeWiseCard.objects.filter(user__isnull=True).first()
        
        if not card:
            # Create a system/default card
            card = TradeWiseCard.objects.create(
                card_number='6734 559',
                capital_available='$500,000',
                partner_name='SPALIS FX',
                contact_number='+254742962615',
                title='TradeWise Premium',
                description='Access premium trading features and exclusive content',
                price_monthly=49.99,
                price_yearly=499.99,
                status='active',
                # user is None for system cards
            )
            print(f"✅ Created new system TradeWise card: {card.card_number}")
        else:
            print(f"✅ Found existing TradeWise card: {card.card_number}")
            
        return card
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in get_or_create_tradewise_card: {e}")
        # Return mock object if database error
        class MockCard:
            card_number = '6734 559'
            capital_available = '$500,000'
            partner_name = 'SPALIS FX'
            contact_number = '+254742962615'
            title = 'TradeWise Premium'
            description = 'Access premium trading features and exclusive content'
            price_monthly = 49.99
            price_yearly = 499.99
            status = 'active'
            
            def save(self):
                pass
        return MockCard()

def get_reviews_context(request=None):
    """Get reviews context safely"""
    try:
        reviews_all = Testimonial.objects.all().order_by('-created_at')
        
        # Reviews statistics
        total_reviews = reviews_all.count()
        approved_reviews = reviews_all.filter(is_approved=True).count()
        pending_reviews = reviews_all.filter(is_approved=False).count()
        featured_reviews = reviews_all.filter(is_featured=True).count()
        
        # Pagination
        if request:
            reviews_page = request.GET.get('reviews_page', 1)
            reviews_paginator = Paginator(reviews_all, 10)
            try:
                reviews = reviews_paginator.page(reviews_page)
            except PageNotAnInteger:
                reviews = reviews_paginator.page(1)
            except EmptyPage:
                reviews = reviews_paginator.page(reviews_paginator.num_pages)
        else:
            reviews = reviews_all[:10]
        
        return {
            'reviews': reviews,
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'pending_reviews': pending_reviews,
            'featured_reviews': featured_reviews,
        }
        
    except Exception as e:
        print(f"⚠️ Error in get_reviews_context: {e}")
        return {
            'reviews': [],
            'total_reviews': 0,
            'approved_reviews': 0,
            'pending_reviews': 0,
            'featured_reviews': 0,
        }

def get_admin_logs_safely():
    """Get admin logs safely - handles case where AdminLog table doesn't exist"""
    try:
        # Try to get recent admin activity
        recent_activity = AdminLog.objects.all().order_by('-timestamp')[:10]
        return recent_activity
    except Exception as e:
        print(f"⚠️ AdminLog query failed, using fallback: {e}")
        # Fallback: return empty list
        return []

def get_affiliate_admin_context():
    """Get affiliate context safely"""
    try:
        return {
            'total_affiliates': Affiliate.objects.count(),
            'pending_payouts_count': PayoutRequest.objects.filter(status='pending').count(),
            'pending_payouts': PayoutRequest.objects.filter(status='pending').select_related('user').order_by('-created_at'),
            'all_affiliates': Affiliate.objects.select_related('user').all().order_by('-created_at'),
            'total_coins_earned': Affiliate.objects.aggregate(Sum('total_coins_earned'))['total_coins_earned__sum'] or 0,
            'total_paid_out': PayoutRequest.objects.filter(status='approved').aggregate(Sum('amount_kes'))['amount_kes__sum'] or 0,
            'current_weekly_number': WeeklyNumber.objects.filter(is_active=True).first(),
            'previous_numbers': WeeklyNumber.objects.filter(is_active=False).order_by('-week_start')[:5],
        }
    except Exception as e:
        print(f"⚠️ Error in get_affiliate_admin_context: {e}")
        return {
            'total_affiliates': 0,
            'pending_payouts_count': 0,
            'pending_payouts': [],
            'all_affiliates': [],
            'total_coins_earned': 0,
            'total_paid_out': 0,
            'current_weekly_number': None,
            'previous_numbers': [],
        }

# ================== BLOG HELPER FUNCTIONS ==================

def get_blog_posts_for_frontend():
    """Get published blog posts for frontend display"""
    try:
        return BlogPost.objects.filter(is_published=True).order_by('-created_at')[:6]
    except Exception as e:
        print(f"⚠️ Error getting blog posts: {e}")
        return []

def get_blog_posts_for_admin():
    """Get all blog posts for admin"""
    try:
        return BlogPost.objects.all().order_by('-created_at')
    except Exception as e:
        print(f"⚠️ Error getting admin blog posts: {e}")
        return []

# ================== SESSION MANAGEMENT SECTION ==================

def get_user_from_session(request):
    """Utility function to get user from session with validation"""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    
    try:
        return Tradeviewusers.objects.get(id=user_id)
    except Tradeviewusers.DoesNotExist:
        # Clear invalid session
        if 'user_id' in request.session:
            del request.session['user_id']
        return None

def is_user_authenticated(request):
    """Check if user is authenticated"""
    return request.session.get('user_id') is not None


# ================== ENHANCED ADMIN AUTHENTICATION WITH ROLE SUPPORT ==================

def enhanced_admin_login(request):
    """Enhanced admin login with TradeWise Number and Role support"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        tradewise_number = request.POST.get('tradewise_number')
        role = request.POST.get('role')
        
        print(f"🔐 ADMIN LOGIN ATTEMPT: User: {username}, Role: {role}, TradeWise: {tradewise_number}")
        
        # Validate all fields
        if not all([username, password, tradewise_number, role]):
            messages.error(request, 'All fields are required.')
            return render(request, 'admin_login.html')
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None and user.is_staff:
            # Verify TradeWise number (you can enhance this with actual validation)
            if verify_admin_tradewise_number(user, tradewise_number):
                login(request, user)
                
                # Store role and tradewise number in session
                request.session['user_role'] = role
                request.session['tradewise_number'] = tradewise_number
                request.session['is_staff_user'] = role == 'staff'
                
                # Log admin login
                create_admin_log(
                    admin_user=user,
                    action='login',
                    model_name='Authentication',
                    description=f'Admin logged in as {role} with TradeWise: {tradewise_number}',
                    request=request
                )
                
                messages.success(request, f'Welcome back, {user.username}! Logged in as {role}.')
                next_url = request.GET.get('next', 'admin_dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid TradeWise number.')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    return render(request, 'admin_login.html', {
        'site_header': 'TradeWise Admin Login'
    })

def verify_admin_tradewise_number(user, tradewise_number):
    """
    Verify TradeWise number for admin users
    You can enhance this with actual database validation
    """
    # Basic validation - you can modify this to check against a database
    if len(tradewise_number) >= 6 and tradewise_number.isalnum():
        return True
    return False

def get_user_role_from_session(request):
    """Utility to get user role from session"""
    return request.session.get('user_role', 'staff')  # Default to staff for security

def is_admin_user_enhanced(user):
    """Enhanced admin check including session role"""
    if not user.is_authenticated or not user.is_staff:
        return False
    
    # In a real implementation, you might check the session role
    # For now, we'll use Django's built-in staff check
    return user.is_staff

def is_full_admin(request):
    """Check if user has full admin privileges"""
    user_role = get_user_role_from_session(request)
    return user_role == 'admin' and request.user.is_staff

def is_staff_user(request):
    """Check if user is staff (limited access)"""
    user_role = get_user_role_from_session(request)
    return user_role == 'staff' and request.user.is_staff

# ================== ROLE-BASED ADMIN DASHBOARD ENHANCEMENT ==================

@login_required
@user_passes_test(is_admin_user_enhanced, login_url='/admin/login/')
def enhanced_admin_dashboard(request):
    """Enhanced admin dashboard with role-based access control"""
    
    # Get user role from session
    user_role = get_user_role_from_session(request)
    is_full_admin_user = is_full_admin(request)
    
    print(f"🎯 DASHBOARD ACCESS: User: {request.user.username}, Role: {user_role}, Full Admin: {is_full_admin_user}")
    
    # Log admin access with role
    create_admin_log(
        admin_user=request.user,
        action='login',
        model_name='Dashboard',
        description=f'Admin accessed dashboard as {user_role}',
        request=request
    )
    
    # Handle POST requests for all CRUD operations
    if request.method == 'POST':
        # Check if user has permission for the action
        if not is_full_admin_user and not is_staff_action_allowed(request):
            messages.error(request, '❌ Access denied. Staff users have limited permissions.')
            return redirect('admin_dashboard')
        
        # Rest of your existing POST handling code remains the same...
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            result = handle_admin_actions(request)
            
            if isinstance(result, JsonResponse):
                return result
                
        except Exception as e:
            print(f"⚠️ Admin action error: {e}")
            if is_ajax:
                return JsonResponse({'success': False, 'error': f'Action failed: {e}'})
            messages.error(request, f'Action failed: {e}')
        
        if not is_ajax:
            return redirect('admin_dashboard')
    
    # GET request - render the dashboard with role context
    try:
        # Your existing GET logic remains the same, but add role context
        total_users = Tradeviewusers.objects.count()
        today = timezone.now().date()
        new_users_today = Tradeviewusers.objects.filter(created_at__date=today).count()
        
        # Get recent activity safely
        recent_activity = get_admin_logs_safely()
        
        # Get other data
        tradewise_card = get_or_create_tradewise_card()
        tradewise_coin = get_or_create_tradewise_coin()
        reviews_context = get_reviews_context(request)
        
        # ✅ ADD BLOG POSTS TO ADMIN CONTEXT
        blog_posts = get_blog_posts_for_admin()
        
        # Calculate revenue stats
        try:
            total_revenue = float(ServiceRevenue.objects.aggregate(total=Sum('amount'))['total'] or 0)
            revenue_today = float(ServiceRevenue.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0)
        except:
            total_revenue = 0
            revenue_today = 0
        
        # Get pending requests
        try:
            pending_consultations = ConsultationRequest.objects.filter(status='pending').count()
            pending_classes = CoachingRequest.objects.filter(status='pending').count()
            pending_services = GeneralServiceRequest.objects.filter(status='pending').count()
            pending_requests_count = pending_consultations + pending_classes + pending_services
        except:
            pending_requests_count = 0
            pending_consultations = 0
            pending_classes = 0
        
        context = {
            'total_users': total_users,
            'new_users_today': new_users_today,
            'total_revenue': total_revenue,
            'revenue_today': revenue_today,
            'pending_requests_count': pending_requests_count,
            'new_requests_today': new_users_today,
            'pending_consultations': pending_consultations,
            'pending_classes': pending_classes,
            'active_traders': total_users,
            'new_traders_today': new_users_today,
            'recent_activity': recent_activity,
            'revenue_chart_data': json.dumps({
                'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'datasets': [{
                    'label': 'Revenue',
                    'data': [12000, 19000, 15000, 25000, 22000, 30000, 28000],
                    'borderColor': '#3498db',
                    'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                }]
            }),
            'service_distribution_data': json.dumps({
                'labels': ['Strategies', 'Signals', 'Classes', 'Consultation'],
                'datasets': [{
                    'data': [35, 25, 20, 20],
                    'backgroundColor': ['#3498db', '#2ecc71', '#e74c3c', '#f39c12'],
                }]
            }),
            'user_growth_percentage': 12,
            'revenue_growth_percentage': 8,
            'requests_percentage': 45,
            'active_traders_percentage': 85,
            'revenue_growth': 15,
            
            # Basic model data
            'strategies': Strategy.objects.all().order_by('-created_at')[:5],
            'signals': Signal.objects.all().order_by('-created_at')[:5],
            'classes': Coaching.objects.all().order_by('-created_at')[:5],
            'services': TradingService.objects.all().order_by('-created_at')[:5],
            'tradewise_card': tradewise_card,
            'tradewise_coin': tradewise_coin,
            'merchandise_list': Merchandise.objects.all().order_by('-created_at')[:5],
            'users': Tradeviewusers.objects.all().order_by('-created_at')[:10],
            
            # ✅ ADD BLOG DATA
            'blog_posts': blog_posts,
            
            # Add reviews data
            **reviews_context,
            
            # Add other data
            'software_list': Software.objects.all().order_by('-created_at')[:5],
            'all_requests': GeneralServiceRequest.objects.all().order_by('-created_at')[:5],
            'service_revenues': ServiceRevenue.objects.all().order_by('-created_at')[:5],
            'affiliate_context': get_affiliate_admin_context(),
            
            # ADD ROLE CONTEXT
            'user_role': user_role,
            'is_full_admin': is_full_admin_user,
            'is_staff_user': not is_full_admin_user,
        }
        
        return render(request, 'admin_dashboard.html', context)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in enhanced_admin_dashboard: {e}")
        context = {
            'total_users': 0,
            'new_users_today': 0,
            'total_revenue': 0,
            'recent_activity': [],
            'user_role': user_role,
            'is_full_admin': is_full_admin_user,
            'is_staff_user': not is_full_admin_user,
            'blog_posts': [],  # ✅ ADD EMPTY BLOG POSTS
        }
        return render(request, 'admin_dashboard.html', context)

def is_staff_action_allowed(request):
    """Check if staff user is allowed to perform the requested action"""
    action = request.POST.get('action', '')
    
    # Staff can only perform these actions
    staff_allowed_actions = [
        'approve_review',
        'toggle_featured', 
        'delete_review',
        'disable_user',
        'enable_user',
        'update_weekly_number',
        'process_payout',
        'add_blog_post',  # ✅ ALLOW STAFF TO ADD BLOG POSTS
        'toggle_blog_publish',  # ✅ ALLOW STAFF TO PUBLISH BLOG POSTS
    ]
    
    return action in staff_allowed_actions


# ================== FIXED ADMIN DASHBOARD FUNCTIONS ==================

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def admin_dashboard_main(request):
    """MAIN ADMIN DASHBOARD - FIXED NAME TO AVOID CONFLICT"""
    
    # Get user role from session (for role-based access)
    user_role = request.session.get('user_role', 'admin')  # Default to admin
    is_staff_user = user_role == 'staff'
    
    print(f"🎯 DASHBOARD ACCESS: User: {request.user.username}, Role: {user_role}, Staff: {is_staff_user}")
    
    # Log admin access
    create_admin_log(
        admin_user=request.user,
        action='login',
        model_name='Dashboard',
        description=f'Admin accessed dashboard as {user_role}',
        request=request
    )
    
    # Handle POST requests for all CRUD operations
    if request.method == 'POST':
        # Check if staff user is trying to perform restricted actions
        if is_staff_user and not is_staff_action_allowed(request):
            messages.error(request, '❌ Access denied. Staff users have limited permissions.')
            return redirect('admin_dashboard')
        
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        try:
            result = handle_admin_actions(request)
            
            if isinstance(result, JsonResponse):
                return result
                
        except Exception as e:
            print(f"⚠️ Admin action error: {e}")
            if is_ajax:
                return JsonResponse({'success': False, 'error': f'Action failed: {e}'})
            messages.error(request, f'Action failed: {e}')
        
        if not is_ajax:
            return redirect('admin_dashboard')
    
    # GET request - render the dashboard with role context
    try:
        # Your existing GET logic remains the same...
        total_users = Tradeviewusers.objects.count()
        today = timezone.now().date()
        new_users_today = Tradeviewusers.objects.filter(created_at__date=today).count()
        
        # Get recent activity safely
        recent_activity = get_admin_logs_safely()
        
        # Get other data
        tradewise_card = get_or_create_tradewise_card()
        tradewise_coin = get_or_create_tradewise_coin()
        reviews_context = get_reviews_context(request)
        
        # ✅ ADD BLOG POSTS TO ADMIN CONTEXT
        blog_posts = get_blog_posts_for_admin()
        
        # Calculate revenue stats
        try:
            total_revenue = float(ServiceRevenue.objects.aggregate(total=Sum('amount'))['total'] or 0)
            revenue_today = float(ServiceRevenue.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0)
        except:
            total_revenue = 0
            revenue_today = 0
        
        # Get pending requests
        try:
            pending_consultations = ConsultationRequest.objects.filter(status='pending').count()
            pending_classes = CoachingRequest.objects.filter(status='pending').count()
            pending_services = GeneralServiceRequest.objects.filter(status='pending').count()
            pending_requests_count = pending_consultations + pending_classes + pending_services
        except:
            pending_requests_count = 0
            pending_consultations = 0
            pending_classes = 0
        
        context = {
            'total_users': total_users,
            'new_users_today': new_users_today,
            'total_revenue': total_revenue,
            'revenue_today': revenue_today,
            'pending_requests_count': pending_requests_count,
            'new_requests_today': new_users_today,
            'pending_consultations': pending_consultations,
            'pending_classes': pending_classes,
            'active_traders': total_users,
            'new_traders_today': new_users_today,
            'recent_activity': recent_activity,
            'revenue_chart_data': json.dumps({
                'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'datasets': [{
                    'label': 'Revenue',
                    'data': [12000, 19000, 15000, 25000, 22000, 30000, 28000],
                    'borderColor': '#3498db',
                    'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                }]
            }),
            'service_distribution_data': json.dumps({
                'labels': ['Strategies', 'Signals', 'Classes', 'Consultation'],
                'datasets': [{
                    'data': [35, 25, 20, 20],
                    'backgroundColor': ['#3498db', '#2ecc71', '#e74c3c', '#f39c12'],
                }]
            }),
            'user_growth_percentage': 12,
            'revenue_growth_percentage': 8,
            'requests_percentage': 45,
            'active_traders_percentage': 85,
            'revenue_growth': 15,
            
            # Basic model data
            'strategies': Strategy.objects.all().order_by('-created_at')[:5],
            'signals': Signal.objects.all().order_by('-created_at')[:5],
            'classes': Coaching.objects.all().order_by('-created_at')[:5],
            'services': TradingService.objects.all().order_by('-created_at')[:5],
            'tradewise_card': tradewise_card,
            'tradewise_coin': tradewise_coin,
            'merchandise_list': Merchandise.objects.all().order_by('-created_at')[:5],
            'users': Tradeviewusers.objects.all().order_by('-created_at')[:10],
            
            # ✅ ADD BLOG DATA
            'blog_posts': blog_posts,
            
            # Add reviews data
            **reviews_context,
            
            # Add other data
            'software_list': Software.objects.all().order_by('-created_at')[:5],
            'all_requests': GeneralServiceRequest.objects.all().order_by('-created_at')[:5],
            'service_revenues': ServiceRevenue.objects.all().order_by('-created_at')[:5],
            'affiliate_context': get_affiliate_admin_context(),
            
            # ADD ROLE CONTEXT FOR TEMPLATE
            'user_role': user_role,
            'is_full_admin': not is_staff_user,
            'is_staff_user': is_staff_user,
        }
        
        return render(request, 'admin_dashboard.html', context)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in admin_dashboard: {e}")
        context = {
            'total_users': 0,
            'new_users_today': 0,
            'total_revenue': 0,
            'recent_activity': [],
            'user_role': user_role,
            'is_full_admin': not is_staff_user,
            'is_staff_user': is_staff_user,
            'blog_posts': [],  # ✅ ADD EMPTY BLOG POSTS
        }
        return render(request, 'admin_dashboard.html', context)


# ================== MERCHANDISE PAYMENT VIEWS ==================

@csrf_exempt
def process_merchandise_payment(request):
    """Process merchandise payment via Paystack"""
    if request.method == 'POST':
        try:
            item_id = request.POST.get('item_id')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            
            # Get merchandise item
            merchandise = get_object_or_404(Merchandise, id=item_id)
            
            # Generate unique reference
            reference = f"MCH{str(uuid.uuid4())[:8].upper()}"
            
            # Create payment record
            payment = MerchPayment.objects.create(
                merchid=merchandise.id,
                phone=phone,
                amount=merchandise.price,
                reference=reference,
                customer_email=email,
                shipping_address=address,
                status='pending'
            )
            
            # Initialize Paystack payment
            paystack = PaystackService()
            callback_url = request.build_absolute_uri(f'/merchandise/payment/verify/{reference}/')
            
            response = paystack.initialize_transaction(
                email=email,
                amount=merchandise.price,
                reference=reference,
                callback_url=callback_url,
                metadata={
                    'merchandise_id': merchandise.id,
                    'product_name': merchandise.name,
                    'payment_type': 'merchandise',
                    'shipping_address': address
                }
            )
            
            if response.get('status'):
                return JsonResponse({
                    'success': True,
                    'authorization_url': response['data']['authorization_url']
                })
            else:
                payment.status = 'failed'
                payment.save()
                return JsonResponse({
                    'success': False,
                    'error': response.get('message', 'Payment initialization failed')
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Payment processing error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def verify_merchandise_payment(request, reference):
    """Verify merchandise payment"""
    try:
        payment = get_object_or_404(MerchPayment, reference=reference)
        merchandise = get_object_or_404(Merchandise, id=payment.merchid)
        
        paystack = PaystackService()
        response = paystack.verify_transaction(reference)
        
        if response.get('status') and response['data']['status'] == 'success':
            payment.status = 'success'
            payment.paystack_reference = response['data']['id']
            payment.save()
            
            # Send order confirmation email
            send_order_confirmation_email(payment, merchandise)
            
            return render(request, 'merchandise/payment_success.html', {
                'payment': payment,
                'merchandise': merchandise
            })
        else:
            payment.status = 'failed'
            payment.save()
            return render(request, 'merchandise/payment_failed.html', {
                'payment': payment,
                'merchandise': merchandise,
                'error': response.get('message', 'Payment verification failed')
            })
            
    except Exception as e:
        return render(request, 'merchandise/payment_error.html', {
            'error': str(e)
        })

def send_order_confirmation_email(payment, merchandise):
    """Send order confirmation email"""
    try:
        subject = f'✅ Order Confirmation - {merchandise.name}'
        message = f"""
Thank you for your order!

Order Details:
- Product: {merchandise.name}
- Price: KES {merchandise.price}
- Order ID: {payment.reference}
- Shipping Address: {payment.shipping_address}

We'll process your order and ship it within 2-3 business days.

Thank you for choosing TradeWise!
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[payment.customer_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Order confirmation email error: {e}")


# ================== ADMIN ACTION HANDLERS SECTION ==================

def handle_admin_actions(request):
    """Handle all admin CRUD operations safely - FIXED VERSION WITH BLOG"""
    action = request.POST.get('action')
    
    print(f"🔄 ADMIN ACTION DETECTED: {action}")
    print(f"📦 POST DATA: {dict(request.POST)}")
    if request.FILES:
        print(f"📁 FILES UPLOADED: {[f.name for f in request.FILES.values()]}")
    
    if not action:
        messages.error(request, '❌ No action specified')
        return
    
    try:
        # Handle review actions
        if action in ['add_review', 'approve_review', 'toggle_featured', 'delete_review']:
            handle_review_admin_actions(request)
        
        # Handle user management actions
        elif action in ['disable_user', 'enable_user']:
            handle_user_management_actions(request)
        
        # Handle affiliate actions
        elif action in ['update_weekly_number', 'process_payout']:
            handle_affiliate_admin_actions(request)
        
        # ✅ FIXED: Handle software uploads
        elif action == 'add_software':
            handle_software_upload(request)
        
        # Handle merchandise actions
        elif action == 'add_merchandise':
            handle_merchandise_upload(request)
            
        elif action == 'delete_merchandise':
            item_id = request.POST.get('item_id')
            merchandise = get_object_or_404(Merchandise, id=item_id)
            merchandise_name = merchandise.name
            merchandise.delete()
            
            create_admin_log(
                admin_user=request.user,
                action='delete',
                model_name='Merchandise',
                description=f'Deleted merchandise: {merchandise_name}',
                object_id=item_id,
                request=request
            )
            
            messages.success(request, 'Merchandise deleted successfully!')
        
        # Handle content management actions
        elif action == 'add_strategy':
            title = request.POST.get('title')
            description = request.POST.get('description')
            price_usd = request.POST.get('price_usd')
            price_kes = request.POST.get('price_kes')
            image = request.FILES.get('image')
            
            print(f"🎯 STRATEGY DATA: title={title}, price_usd={price_usd}, price_kes={price_kes}")
            
            # Validate required fields
            if not title or not description:
                messages.error(request, '❌ Title and description are required for strategies')
                return
                
            if not price_usd or not price_kes:
                messages.error(request, '❌ Both USD and KES prices are required')
                return
            
            # Convert prices to decimal
            try:
                price_usd = float(price_usd)
                price_kes = float(price_kes)
            except (ValueError, TypeError):
                messages.error(request, '❌ Prices must be valid numbers')
                return
            
            strategy = Strategy.objects.create(
                title=title,
                description=description,
                price_usd=price_usd,
                price_kes=price_kes,
                image=image
            )
            
            create_admin_log(
                admin_user=request.user,
                action='create',
                model_name='Strategy',
                description=f'Created strategy: {title}',
                object_id=str(strategy.id),
                request=request
            )
            
            messages.success(request, '✅ Strategy added successfully!')
            
        elif action == 'delete_strategy':
            item_id = request.POST.get('item_id')
            strategy = get_object_or_404(Strategy, id=item_id)
            strategy_title = strategy.title
            strategy.delete()
            
            create_admin_log(
                admin_user=request.user,
                action='delete',
                model_name='Strategy',
                description=f'Deleted strategy: {strategy_title}',
                object_id=item_id,
                request=request
            )
            
            messages.success(request, 'Strategy deleted successfully!')
            
        elif action == 'add_signal':
            title = request.POST.get('title')
            description = request.POST.get('description')
            price_usd = request.POST.get('price_usd')
            price_kes = request.POST.get('price_kes')
            image = request.FILES.get('image')
            
            print(f"🎯 SIGNAL DATA: title={title}, price_usd={price_usd}, price_kes={price_kes}")
            
            # Validate required fields
            if not title or not description:
                messages.error(request, '❌ Title and description are required for signals')
                return
                
            if not price_usd or not price_kes:
                messages.error(request, '❌ Both USD and KES prices are required')
                return
            
            # Convert prices to decimal
            try:
                price_usd = float(price_usd)
                price_kes = float(price_kes)
            except (ValueError, TypeError):
                messages.error(request, '❌ Prices must be valid numbers')
                return
            
            signal = Signal.objects.create(
                title=title,
                description=description,
                price_usd=price_usd,
                price_kes=price_kes,
                image=image,
                accuracy_forex=80,  # ✅ ADDED REQUIRED FIELD
                accuracy_crypto=60  # ✅ ADDED REQUIRED FIELD
            )
            
            create_admin_log(
                admin_user=request.user,
                action='create',
                model_name='Signal',
                description=f'Created signal: {title}',
                object_id=str(signal.id),
                request=request
            )
            
            messages.success(request, '✅ Signal added successfully!')
            
        elif action == 'delete_signal':
            item_id = request.POST.get('item_id')
            signal = get_object_or_404(Signal, id=item_id)
            signal_title = signal.title
            signal.delete()
            
            create_admin_log(
                admin_user=request.user,
                action='delete',
                model_name='Signal',
                description=f'Deleted signal: {signal_title}',
                object_id=item_id,
                request=request
            )
            
            messages.success(request, 'Signal deleted successfully!')
            
        # Handle class actions
        elif action == 'add_class':
            title = request.POST.get('title')
            description = request.POST.get('description')
            price = request.POST.get('price')
            duration = request.POST.get('duration')
            image = request.FILES.get('image')
            
            if not title or not description or not price:
                messages.error(request, '❌ Title, description, and price are required for classes')
                return
            
            try:
                price = float(price)
            except (ValueError, TypeError):
                messages.error(request, '❌ Price must be a valid number')
                return
            
            trading_class = TradingClass.objects.create(
                title=title,
                description=description,
                price=price,
                duration=duration or '4 weeks',
                image=image
            )
            
            create_admin_log(
                admin_user=request.user,
                action='create',
                model_name='TradingClass',
                description=f'Created class: {title}',
                object_id=str(trading_class.id),
                request=request
            )
            
            messages.success(request, '✅ Trading class added successfully!')
            
        elif action == 'delete_class':
            item_id = request.POST.get('item_id')
            trading_class = get_object_or_404(TradingClass, id=item_id)
            class_title = trading_class.title
            trading_class.delete()
            
            create_admin_log(
                admin_user=request.user,
                action='delete',
                model_name='TradingClass',
                description=f'Deleted class: {class_title}',
                object_id=item_id,
                request=request
            )
            
            messages.success(request, 'Trading class deleted successfully!')
            
        # ✅ BLOG MANAGEMENT ACTIONS - ADDED
        elif action == 'add_blog_post':
            title = request.POST.get('title')
            content = request.POST.get('content')
            excerpt = request.POST.get('excerpt', '')
            image = request.FILES.get('image')
            is_published = request.POST.get('is_published') == 'on'
            
            if not title or not content:
                messages.error(request, '❌ Title and content are required for blog posts')
                return
            
            blog_post = BlogPost.objects.create(
                title=title,
                content=content,
                excerpt=excerpt,
                image=image,
                is_published=is_published,
                status='published' if is_published else 'draft'
            )
            
            create_admin_log(
                admin_user=request.user,
                action='create',
                model_name='BlogPost',
                description=f'Created blog post: {title}',
                object_id=str(blog_post.id),
                request=request
            )
            
            messages.success(request, '✅ Blog post added successfully!')
            
        elif action == 'delete_blog_post':
            post_id = request.POST.get('post_id')
            blog_post = get_object_or_404(BlogPost, id=post_id)
            post_title = blog_post.title
            blog_post.delete()
            
            create_admin_log(
                admin_user=request.user,
                action='delete',
                model_name='BlogPost',
                description=f'Deleted blog post: {post_title}',
                object_id=post_id,
                request=request
            )
            
            messages.success(request, 'Blog post deleted successfully!')
            
        elif action == 'toggle_blog_publish':
            post_id = request.POST.get('post_id')
            blog_post = get_object_or_404(BlogPost, id=post_id)
            blog_post.is_published = not blog_post.is_published
            blog_post.status = 'published' if blog_post.is_published else 'draft'
            blog_post.save()
            
            status = 'published' if blog_post.is_published else 'unpublished'
            create_admin_log(
                admin_user=request.user,
                action='update',
                model_name='BlogPost',
                description=f'{status.capitalize()} blog post: {blog_post.title}',
                object_id=post_id,
                request=request
            )
            
            messages.success(request, f'Blog post {status} successfully!')
            
        # ✅ FIXED CARD UPDATE SECTION
        elif action == 'update_card':
            # Get or create system card (user=None)
            card = TradeWiseCard.objects.filter(user__isnull=True).first()
            
            if not card:
                # Create new system card
                card = TradeWiseCard()
            
            # Update all fields from form data
            card.card_number = request.POST.get('card_number', '6734 559')
            card.capital_available = request.POST.get('capital_available', '$500,000')
            card.partner_name = request.POST.get('partner_name', 'SPALIS FX')
            card.contact_number = request.POST.get('contact_number', '+254742962615')
            card.title = request.POST.get('title', 'TradeWise Premium')
            card.description = request.POST.get('description', 'Access premium trading features')
            
            # Handle numeric fields with validation
            try:
                card.price_monthly = float(request.POST.get('price_monthly', 49.99))
            except (ValueError, TypeError):
                card.price_monthly = 49.99
                
            try:
                card.price_yearly = float(request.POST.get('price_yearly', 499.99))
            except (ValueError, TypeError):
                card.price_yearly = 499.99
            
            # Handle image upload
            if 'image' in request.FILES:
                card.image = request.FILES['image']
            
            # Ensure it's a system card
            card.user = None
            
            card.save()
            
            print(f"✅ SUCCESS: Card updated - {card.card_number}, {card.capital_available}")
            
            create_admin_log(
                admin_user=request.user,
                action='update',
                model_name='TradeWiseCard',
                description='Updated TradeWise card details',
                object_id=str(card.id),
                request=request
            )
            
            messages.success(request, '✅ Card details updated successfully!')
            
        elif action == 'update_coin':
            coin = get_or_create_tradewise_coin()
            coin.coin_symbol = request.POST.get('coin_symbol', 'TWC')
            coin.coin_name = request.POST.get('coin_name', 'TradeWise Coin')
            coin.transaction_type = request.POST.get('transaction_type', 'BUY')
            
            try:
                coin.quantity = float(request.POST.get('quantity', 1000.00000000))
                coin.price = float(request.POST.get('price', 0.10))
            except (ValueError, TypeError):
                messages.error(request, '❌ Quantity and price must be valid numbers')
                return
                
            coin.notes = request.POST.get('notes', '')
            coin.save()
            
            create_admin_log(
                admin_user=request.user,
                action='update',
                model_name='TradeWiseCoin',
                description='Updated TradeWise coin details',
                object_id=str(coin.id),
                request=request
            )
            
            messages.success(request, '✅ Coin details updated successfully!')
            
        else:
            messages.error(request, f'❌ Unknown action: {action}')
            
    except Exception as e:
        print(f"❌ DETAILED ERROR in handle_admin_actions: {e}")
        print(f"🔍 TRACEBACK:")
        import traceback
        traceback.print_exc()
        
        # Show SPECIFIC error message to user
        messages.error(request, f'❌ Upload failed: {str(e)}')

def handle_software_upload(request):
    """Handle software uploads with detailed error reporting"""
    try:
        name = request.POST.get('name')
        description = request.POST.get('description')
        version = request.POST.get('version')
        file_type = request.POST.get('file_type')
        software_file = request.FILES.get('file')
        thumbnail = request.FILES.get('thumbnail')
        
        print(f"🎯 SOFTWARE UPLOAD DATA: name={name}, version={version}, file_type={file_type}")
        print(f"📁 FILE: {software_file.name if software_file else 'No file'}")
        print(f"🖼️ THUMBNAIL: {thumbnail.name if thumbnail else 'No thumbnail'}")
        
        # Validate required fields
        if not name or not description or not version or not file_type:
            messages.error(request, '❌ All software fields are required')
            return
            
        if not software_file:
            messages.error(request, '❌ Software file is required')
            return
        
        # Create software entry
        software = Software.objects.create(
            name=name,
            description=description,
            version=version,
            file_type=file_type,
            file=software_file,
            thumbnail=thumbnail
        )
        
        create_admin_log(
            admin_user=request.user,
            action='create',
            model_name='Software',
            description=f'Uploaded software: {name} v{version}',
            object_id=str(software.id),
            request=request
        )
        
        messages.success(request, f'✅ Software "{name}" uploaded successfully!')
        
    except Exception as e:
        print(f"❌ SOFTWARE UPLOAD ERROR: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'❌ Software upload failed: {str(e)}')

def handle_merchandise_upload(request):
    """Handle merchandise uploads with detailed error reporting"""
    try:
        name = request.POST.get('name')
        category = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        
        print(f"🎯 MERCHANDISE UPLOAD DATA: name={name}, category={category}, price={price}")
        print(f"🖼️ IMAGE: {image.name if image else 'No image'}")
        
        # Validate required fields
        if not name or not category or not description or not price:
            messages.error(request, '❌ All merchandise fields are required')
            return
            
        if not image:
            messages.error(request, '❌ Product image is required')
            return
        
        # Convert price to integer
        try:
            price = int(price)
        except (ValueError, TypeError):
            messages.error(request, '❌ Price must be a valid number')
            return
        
        # Create merchandise entry
        merchandise = Merchandise.objects.create(
            name=name,
            category=category,
            description=description,
            price=price,
            image=image
        )
        
        create_admin_log(
            admin_user=request.user,
            action='create',
            model_name='Merchandise',
            description=f'Added merchandise: {name}',
            object_id=str(merchandise.id),
            request=request
        )
        
        messages.success(request, f'✅ Merchandise "{name}" added successfully!')
        
    except Exception as e:
        print(f"❌ MERCHANDISE UPLOAD ERROR: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'❌ Merchandise upload failed: {str(e)}')

def handle_review_admin_actions(request):
    """Handle review-related admin actions"""
    action = request.POST.get('action')
    
    try:
        if action == 'add_review':
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            user_role = request.POST.get('user_role', 'Trader')
            rating = request.POST.get('rating')
            review_text = request.POST.get('review_text', '').strip()
            avatar = request.FILES.get('avatar')
            is_approved = request.POST.get('is_approved') == 'on'
            is_featured = request.POST.get('is_featured') == 'on'
            
            if not name or not review_text or not rating:
                messages.error(request, '❌ Name, review text, and rating are required')
                return
            
            review = Testimonial.objects.create(
                author_name=name,
                email=email if email else None,
                user_role=user_role,
                rating=int(rating),
                content=review_text,
                image=avatar,
                is_approved=is_approved,
                is_featured=is_featured,
                from_admin=True,
                is_active=True
            )
            
            create_admin_log(
                admin_user=request.user,
                action='create',
                model_name='Testimonial',
                description=f'Added review from {name}',
                object_id=str(review.id),
                request=request
            )
            
            messages.success(request, f'✅ Review from {name} added successfully!')
            
        elif action == 'approve_review':
            review_id = request.POST.get('review_id')
            review = get_object_or_404(Testimonial, id=review_id)
            review.is_approved = True
            review.save()
            
            create_admin_log(
                admin_user=request.user,
                action='update',
                model_name='Testimonial',
                description=f'Approved review from {review.author_name}',
                object_id=review_id,
                request=request
            )
            
            messages.success(request, f'✅ Review from {review.author_name} approved!')
            
        elif action == 'toggle_featured':
            review_id = request.POST.get('review_id')
            feature = request.POST.get('feature') == 'true'
            review = get_object_or_404(Testimonial, id=review_id)
            review.is_featured = feature
            review.save()
            
            action_text = 'featured' if feature else 'unfeatured'
            
            create_admin_log(
                admin_user=request.user,
                action='update',
                model_name='Testimonial',
                description=f'{action_text.capitalize()} review from {review.author_name}',
                object_id=review_id,
                request=request
            )
            
            messages.success(request, f'✅ Review {action_text} successfully!')
            
        elif action == 'delete_review':
            review_id = request.POST.get('review_id')
            review = get_object_or_404(Testimonial, id=review_id)
            author_name = review.author_name
            review.delete()
            
            create_admin_log(
                admin_user=request.user,
                action='delete',
                model_name='Testimonial',
                description=f'Deleted review from {author_name}',
                object_id=review_id,
                request=request
            )
            
            messages.success(request, f'✅ Review from {author_name} deleted!')
            
    except Exception as e:
        print(f"❌ Error in handle_review_admin_actions: {e}")
        messages.error(request, f'❌ Error processing review action: {str(e)}')

def handle_user_management_actions(request):
    """Handle user management operations"""
    action = request.POST.get('action')
    user_id = request.POST.get('user_id')
    
    try:
        user = get_object_or_404(Tradeviewusers, id=user_id)
        
        if action == 'disable_user':
            user.is_active = False
            user.save()
            
            create_admin_log(
                admin_user=request.user,
                action='user_disabled',
                model_name='Tradeviewusers',
                description=f'Disabled user account: {user.email}',
                object_id=user_id,
                request=request
            )
            
            messages.success(request, f'User account {user.email} has been disabled.')
            
        elif action == 'enable_user':
            user.is_active = True
            user.save()
            
            create_admin_log(
                admin_user=request.user,
                action='user_enabled',
                model_name='Tradeviewusers',
                description=f'Enabled user account: {user.email}',
                object_id=user_id,
                request=request
            )
            
            messages.success(request, f'User account {user.email} has been enabled.')
            
    except Exception as e:
        print(f"❌ Error in handle_user_management_actions: {e}")
        messages.error(request, f'❌ Error processing user action: {str(e)}')

def handle_affiliate_admin_actions(request):
    """Handle affiliate-related admin actions"""
    action = request.POST.get('action')
    
    try:
        if action == 'update_weekly_number':
            number = request.POST.get('weekly_number')
            week_start = request.POST.get('week_start')
            
            if number and week_start:
                WeeklyNumber.objects.filter(is_active=True).update(is_active=False)
                weekly_number = WeeklyNumber.objects.create(
                    number=number,
                    week_start=week_start,
                    is_active=True
                )
                
                create_admin_log(
                    admin_user=request.user,
                    action='update',
                    model_name='WeeklyNumber',
                    description=f'Updated weekly number to {number}',
                    object_id=str(weekly_number.id),
                    request=request
                )
                
                messages.success(request, f'✅ Weekly number updated to {number} successfully!')
                
        elif action == 'process_payout':
            payout_id = request.POST.get('payout_id')
            status = request.POST.get('status')
            
            payout = get_object_or_404(PayoutRequest, id=payout_id)
            payout.status = status
            payout.processed_by = request.user
            payout.processed_at = timezone.now()
            payout.save()
            
            create_admin_log(
                admin_user=request.user,
                action='update',
                model_name='PayoutRequest',
                description=f'Processed payout #{payout_id} as {status}',
                object_id=payout_id,
                request=request
            )
            
            if status == 'approved':
                messages.success(request, f'✅ Payout #{payout_id} approved successfully!')
            else:
                messages.warning(request, f'Payout #{payout_id} rejected.')
                
    except Exception as e:
        print(f"❌ Error in handle_affiliate_admin_actions: {e}")
        messages.error(request, f'❌ Error processing affiliate action: {str(e)}')


# ================== AUTHENTICATION & USER MANAGEMENT SECTION ==================

def send_admin_notification(user):
    """Send admin notification about new user registration"""
    try:
        subject = '🔥 NEW USER REGISTERED - TradeWise'
        message = f"""
🚀 NEW USER REGISTERED ON TRADEWISE

👤 User Details:
- Name: {user.first_name} {user.second_name}
- Email: {user.email}
- Phone: {user.phone}
- TradeWise Number: {user.account_number}
- Registered: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 Total Users: {Tradeviewusers.objects.count()}

Login to admin dashboard to view details.
        """
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[admin_email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"Admin notification email error: {e}")
        return False

def index(request):
    """Home page view WITH BLOG POSTS"""
    analysis = ForexAnalysis.objects.all().order_by('-created_at')
    tradewise_card = get_or_create_tradewise_card()
    tradewise_coin = get_or_create_tradewise_coin()

    # Merchandise data
    all_categories = ['caps-hats', 'hoodies', 't-shirts', 'accessories']
    
    category_items = {}
    for category in all_categories:
        try:
            item = Merchandise.objects.filter(category=category, is_active=True).first()
            category_items[category] = item
        except:
            category_items[category] = None
    
    # Testimonials
    testimonials = Testimonial.objects.filter(is_active=True, is_featured=True)[:5]
    
    # Trading classes
    trading_classes = TradingClass.objects.filter(is_active=True)[:4]
    
    # ✅ BLOG POSTS - ADDED
    blog_posts = get_blog_posts_for_frontend()
    
    context = {
        'analysis': analysis,
        'tradewise_coin': tradewise_coin,
        'tradewise_card': tradewise_card,
        'all_categories': all_categories,
        'category_items': category_items,
        'testimonials': testimonials,
        'trading_classes': trading_classes,
        'blog_posts': blog_posts,  # ✅ ADDED
    }
    return render(request, "index.html", context)

def login_page(request):
    """Show the login/signup page"""
    return render(request, "login.html")

def account(request):
    """User account page"""
    user = get_user_from_session(request)
    if not user:
        messages.error(request, 'Please sign in to access your account.')
        return redirect('login_page')

    try:
        analysis = ForexAnalysis.objects.all().order_by('-created_at')
        balance = user.capital_access.balance if hasattr(user, 'capital_access') else 0.00
        
        # Affiliate profile
        affiliate, created = Affiliate.objects.get_or_create(user=user)
        cash_value = affiliate.coin_balance * 10
        
        # Referral stats
        pending_referrals = affiliate.referrals.filter(status='pending').count()
        approved_referrals = affiliate.referrals.filter(status='approved').count()
        
        referral_stats = {
            'total_referrals': affiliate.total_referrals,
            'total_coins': affiliate.total_coins_earned,
            'pending_coins': pending_referrals * 50,
            'approved_referrals': approved_referrals,
            'coin_balance': affiliate.coin_balance,
        }
        
        # Weekly number
        weekly_number = WeeklyNumber.objects.filter(is_active=True).first()
        
        # Payout history
        payout_history = PayoutRequest.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Notifications
        notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:10]
        
        context = {
            'account_number': user.account_number,
            'balance': balance,
            'first_name': user.first_name,
            'second_name': user.second_name,
            'email': user.email,
            'phone': user.phone,
            'analysis': analysis,
            'user_referral_link': f"http://127.0.0.1:8000/signup?ref={affiliate.referral_code}",
            'referral_stats': referral_stats,
            'weekly_number': weekly_number,
            'user_id': user.id,
            'cash_value': cash_value,
            'payout_history': payout_history,
            'affiliate': affiliate,
            'notifications': notifications,
        }
        return render(request, 'account.html', context)
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('login_page')

def signup(request):
    """User registration - FIXED VERSION"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        second_name = request.POST.get('second_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')  # ✅ ADDED PHONE FIELD
        referral_code = request.POST.get('referral_code')

        print(f"🔐 SIGNUP ATTEMPT: {first_name} {second_name}, Email: {email}, Phone: {phone}")

        # Validate required fields
        if not all([first_name, second_name, email, password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'login.html')

        # Validate password strength
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'login.html')

        # Check if email already exists
        if Tradeviewusers.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return render(request, 'login.html')

        try:
            # Create user with phone field
            user = Tradeviewusers.objects.create(
                first_name=first_name.strip(),
                second_name=second_name.strip(),
                email=email.strip().lower(),
                password=password,
                phone=phone.strip() if phone else None
            )
            
            print(f"✅ USER CREATED: {user.account_number}, {user.email}")

            # Create capital access
            CapitalAccess.objects.create(user=user, balance=0.00)
            print("✅ CAPITAL ACCESS CREATED")

            # Handle referral
            if referral_code:
                try:
                    referrer_affiliate = Affiliate.objects.get(referral_code=referral_code.strip())
                    Referral.objects.create(
                        referrer=referrer_affiliate,
                        referred_user=user,
                        coins_earned=50,
                        status='pending'
                    )
                    messages.info(request, 'Referral applied! You will receive coins once your account is verified.')
                    print(f"✅ REFERRAL APPLIED: {referral_code}")
                except Affiliate.DoesNotExist:
                    messages.warning(request, 'Invalid referral code.')
                    print("❌ INVALID REFERRAL CODE")
            
            # Send verification email
            email_sent = user.send_verification_email()
            print(f"✅ VERIFICATION EMAIL SENT: {email_sent}")

            # Send admin notification
            admin_notified = send_admin_notification(user)
            print(f"✅ ADMIN NOTIFIED: {admin_notified}")

            # Send welcome email
            welcome_sent = user.send_welcome_email(password)
            print(f"✅ WELCOME EMAIL SENT: {welcome_sent}")

            if email_sent:
                messages.success(request, 'Account created successfully! Please check your email to verify your account.')
            else:
                messages.warning(request, 'Account created successfully! But we could not send verification email. Please contact support.')
            
            return redirect('login_page')
            
        except ValidationError as e:
            print(f"❌ VALIDATION ERROR: {e}")
            messages.error(request, f'Error: {e}')
            return render(request, 'login.html')
        except Exception as e:
            print(f"❌ SIGNUP ERROR: {e}")
            messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'login.html')

    return render(request, 'login.html')

def login_view(request):
    """User login - FIXED VERSION WITH DEBUGGING"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        print(f"🔐 LOGIN ATTEMPT: Email: {email}")

        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'login.html')

        try:
            user = Tradeviewusers.objects.get(email=email.strip().lower())
            print(f"✅ USER FOUND: {user.email}, Verified: {user.is_email_verified}, Active: {user.is_active}")

            # Check if user is active
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Please contact support.')
                print("❌ ACCOUNT DEACTIVATED")
                return render(request, 'login.html')
            
            # Check if email is verified
            if not user.is_email_verified:
                messages.error(request, 'Please verify your email address before logging in. Check your email for verification link.')
                print("❌ EMAIL NOT VERIFIED")
                return render(request, 'login.html')
            
            # Check password
            if user.check_password(password):
                request.session['user_id'] = user.id
                user.last_login = timezone.now()
                user.save()
                
                print(f"✅ LOGIN SUCCESS: {user.first_name}, Session: {request.session.get('user_id')}")
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('account')
            else:
                print("❌ INVALID PASSWORD")
                messages.error(request, 'Invalid email or password.')
                
        except Tradeviewusers.DoesNotExist:
            print("❌ USER NOT FOUND")
            messages.error(request, 'Invalid email or password.')
        except Exception as e:
            print(f"❌ LOGIN ERROR: {e}")
            messages.error(request, 'An error occurred during login. Please try again.')

    return render(request, 'login.html')

def logout_view(request):
    """User logout - FIXED VERSION"""
    user_id = request.session.get('user_id')
    
    # Clear all session data
    if 'user_id' in request.session:
        del request.session['user_id']
    
    # Clear any other session data you might have
    for key in list(request.session.keys()):
        del request.session[key]
    
    if user_id:
        try:
            user = Tradeviewusers.objects.get(id=user_id)
            messages.success(request, f'You have been logged out successfully. See you soon, {user.first_name}!')
        except Tradeviewusers.DoesNotExist:
            messages.success(request, 'You have been logged out successfully.')
    else:
        messages.success(request, 'You have been logged out successfully.')
    
    return redirect('index')


# ================== EMAIL VERIFICATION & PASSWORD RESET SECTION ==================

def verify_email(request, token):
    """Verify user email address"""
    try:
        user = Tradeviewusers.objects.get(email_verification_token=token)
        user.is_email_verified = True
        user.email_verification_token = None
        user.save()
        
        print(f"✅ EMAIL VERIFIED: {user.email}")
        
        # Auto-approve pending referrals
        pending_referrals = Referral.objects.filter(referred_user=user, status='pending')
        
        if pending_referrals.exists():
            for referral in pending_referrals:
                referral.status = 'approved'
                referral.save()
                
                # Award coins to referrer
                affiliate = referral.referrer
                affiliate.total_coins_earned += referral.coins_earned
                affiliate.coin_balance += referral.coins_earned
                affiliate.total_referrals += 1
                affiliate.save()
                
            print(f"✅ REFERRALS APPROVED: {pending_referrals.count()} referrals approved")
        
        messages.success(request, 'Email verified successfully! You can now log in to your account.')
        return redirect('login_page')
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
        return redirect('login_page')

def forgot_password(request):
    """Handle password reset request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = Tradeviewusers.objects.get(email=email)
            email_sent = user.send_password_reset_email()
            
            if email_sent:
                messages.success(request, 'Password reset link has been sent to your email.')
            else:
                messages.error(request, 'Failed to send password reset email. Please try again later.')
            return redirect('login_page')
        except Tradeviewusers.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return redirect('login_page')
    
    return render(request, 'forgot_password.html')

def reset_password(request, token):
    """Handle password reset confirmation"""
    try:
        user = Tradeviewusers.objects.get(password_reset_token=token)
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'reset_password.html', {'token': token})
            
            if len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'reset_password.html', {'token': token})
            
            user.password = make_password(new_password)
            user.password_reset_token = None
            user.save()
            
            messages.success(request, 'Password reset successfully! You can now log in with your new password.')
            return redirect('login_page')
        
        return render(request, 'reset_password.html', {'token': token})
    
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'Invalid or expired password reset token.')
        return redirect('login_page')


# ================== WEBSITE PAGES SECTION ==================

def coaching(request):
    """Coaching page"""
    coaching_programs = Coaching.objects.filter(is_active=True).order_by('-created_at')
    trading_classes = TradingClass.objects.filter(is_active=True).order_by('-created_at')
    
    context = {
        'coaching_programs': coaching_programs,
        'trading_classes': trading_classes,
    }
    return render(request, 'coaching.html', context)

def market(request):
    """Market page"""
    return render(request, 'market_hub.html')

def trade(request):
    """Trade desk page"""
    return render(request, 'trade_desk.html')

def contact(request):
    """Contact page"""
    faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order')
    return render(request, 'contact.html', {'faqs': faqs})

def merchandise(request):
    """Merchandise page"""
    all_categories = ['caps-hats', 'hoodies', 't-shirts', 'accessories']
    
    category_items = {}
    for category in all_categories:
        try:
            item = Merchandise.objects.filter(category=category, is_active=True).first()
            category_items[category] = item
        except:
            category_items[category] = None
    
    category_items_grid = {}
    for category in all_categories:
        items = Merchandise.objects.filter(category=category, is_active=True)[:8]
        category_items_grid[category] = items
    
    context = {
        'all_categories': all_categories,
        'category_items': category_items,
        'category_items_grid': category_items_grid,
        'featured_items': category_items,
    }
    return render(request, 'merchandise.html', context)

def merchandise_by_category(request, category):
    """Merchandise by category"""
    items = Merchandise.objects.filter(category=category, is_active=True).order_by('-created_at')
    category_display = dict(Merchandise.CATEGORY_CHOICES).get(category, "Merchandise")
    return render(request, 'shop.html', {
        'items': items,
        'category_name': category_display,
    })

def services_page(request):
    """Services page"""
    strategies = Strategy.objects.filter(is_active=True)
    signals = Signal.objects.filter(is_active=True)
    trading_services = TradingService.objects.filter(is_active=True)
    
    context = {
        'strategies': strategies,
        'signals': signals,
        'trading_services': trading_services,
    }
    return render(request, 'services_page.html', context)

def classes_view(request):
    """Classes view"""
    coaching_programs = Coaching.objects.filter(is_active=True).order_by('-created_at')
    trading_classes = TradingClass.objects.filter(is_active=True).order_by('-created_at')

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        class_type = request.POST.get('class_type')
        message = request.POST.get('message', '')

        CoachingRequest.objects.create(
            name=name,
            email=email,
            phone=phone,
            class_type=class_type,
            message=message
        )
        
        messages.success(request, "Your coaching booking request has been submitted successfully!")
        return render(request, 'classes.html', {
            'coaching_programs': coaching_programs,
            'trading_classes': trading_classes
        })

    return render(request, 'classes.html', {
        'coaching_programs': coaching_programs,
        'trading_classes': trading_classes
    })

def submit_class_request(request):
    """Handle class requests"""
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        class_type = request.POST.get('class_type')
        message = request.POST.get('message', '')

        CoachingRequest.objects.create(
            name=name,
            email=email,
            phone=phone,
            class_type=class_type,
            message=message
        )
        
        messages.success(request, "Your class request has been submitted successfully!")
        return redirect('classes')
    
    return redirect('classes')

def analysis_detail(request, pk):
    """Analysis detail page"""
    analysis = get_object_or_404(ForexAnalysis, pk=pk)
    return render(request, 'analysis.html', {'analysis': analysis})

def payment(request):
    """Payment page"""
    return render(request, 'payment.html')

def merchandise_payment(request, id):
    """Merchandise payment"""
    merch = get_object_or_404(Merchandise, pk=id)
    request.session['merch_id'] = merch.id
    request.session['amount'] = float(merch.price)
    return render(request, 'payment1.html', {'merch': merch, 'amount': merch.price})

def submit_consultation(request):
    """Submit consultation request"""
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        class_interest = request.POST.get("class_interest", "")
        message = request.POST.get("message", "")

        ConsultationRequest.objects.create(
            name=name,
            email=email,
            phone=phone,
            class_interest=class_interest,
            message=message
        )

        try:
            send_mail(
                subject="New Consultation Request",
                message=f"Name: {name}\nEmail: {email}\nPhone: {phone}\nClass: {class_interest}\nMessage: {message}",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                recipient_list=[getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')],
                fail_silently=False,
            )
        except Exception as e:
            print(f"EMAIL ERROR: {e}")

        messages.success(request, "Your consultation request has been submitted successfully.")
        return redirect('contact')

    return redirect('contact')

@csrf_exempt
def submit_service_request(request):
    """Handle service request submissions"""
    if request.method == 'POST':
        try:
            name = request.POST.get("name")
            email = request.POST.get("email")
            phone = request.POST.get("phone")
            service_type = request.POST.get("service_type")
            selected_service = request.POST.get("selected_service")
            experience = request.POST.get("experience")
            message = request.POST.get("message", "")
            
            # Determine service price
            service_prices = {
                'Strategy': 500,
                'Signal': 300,
                'Custom Strategy Development': 1000,
                'Premium Signal Service': 500,
            }
            
            service_price = service_prices.get(selected_service, 200)

            # Create service request
            service_request = GeneralServiceRequest.objects.create(
                name=name,
                email=email,
                phone=phone,
                service_type=service_type,
                selected_service=selected_service,
                experience_level=experience,
                message=message,
                status='pending'
            )

            # Create revenue record
            revenue = ServiceRevenue.objects.create(
                service_type=f"{service_type} - {selected_service}",
                client_name=name,
                client_email=email,
                client_phone=phone,
                amount=service_price,
                notes=f"Experience: {experience}\nMessage: {message}",
                status='pending'
            )

            # Send email notification
            try:
                subject = f'💰 NEW SERVICE REQUEST: {service_type} - {selected_service}'
                email_message = f"""
🚀 NEW SERVICE REQUEST & REVENUE COMMITMENT

💰 Revenue Commitment: ${service_price}
📋 Service Type: {service_type}
🎯 Selected Service: {selected_service}
👤 Client: {name}
📧 Email: {email}
📞 Phone: {phone}
📊 Experience Level: {experience}
📝 Message: {message or "No additional notes"}

⏰ Submitted: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
🔗 Request ID: {service_request.id}
                """
                
                admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
                
                send_mail(
                    subject=subject,
                    message=email_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
                    recipient_list=[admin_email],
                    fail_silently=False,
                )
                
            except Exception as e:
                print(f"Email sending failed: {e}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Your {selected_service} request has been submitted successfully! We will contact you within 24 hours.',
                    'request_id': service_request.id
                })
            else:
                messages.success(request, f"Your {selected_service} request has been submitted successfully! We will contact you within 24 hours.")
                return redirect('market_hub')

        except Exception as e:
            print(f"Service request error: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'There was an error submitting your request. Please try again.'
                }, status=400)
            else:
                messages.error(request, "There was an error submitting your request. Please try again.")
                return redirect('market_hub')
    
    return redirect('market_hub')

def learning_hub(request):
    """Learning Hub page"""
    classes = Coaching.objects.filter(is_active=True).order_by('-created_at')
    trading_classes = TradingClass.objects.filter(is_active=True).order_by('-created_at')
    strategies = Strategy.objects.filter(is_active=True).order_by('-created_at')[:3]
    signals = Signal.objects.filter(is_active=True).order_by('-created_at')[:2]
    
    context = {
        'classes': classes,
        'trading_classes': trading_classes,
        'strategies': strategies,
        'signals': signals,
    }
    return render(request, 'learning_hub.html', context)

def market_hub(request):
    """Market Hub page"""
    strategies = Strategy.objects.filter(is_active=True).order_by('-created_at')
    signals = Signal.objects.filter(is_active=True).order_by('-created_at')
    software_list = Software.objects.filter(is_active=True).order_by('-created_at')
    trading_services = TradingService.objects.filter(is_active=True).order_by('-created_at')
    
    context = {
        'strategies': strategies,
        'signals': signals,
        'software_list': software_list,
        'trading_services': trading_services,
    }
    return render(request, 'market_hub.html', context)


# ================== BLOG VIEWS SECTION ==================

def blog_page(request):
    """Blog page with all published posts"""
    blog_posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(blog_posts, 9)  # 9 posts per page
    page = request.GET.get('page')
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    context = {
        'blog_posts': posts,
        'total_posts': blog_posts.count(),
    }
    return render(request, 'blog.html', context)

def blog_detail(request, slug):
    """Blog post detail page"""
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    
    # Get related posts (same category or recent)
    related_posts = BlogPost.objects.filter(
        is_published=True
    ).exclude(id=post.id).order_by('-created_at')[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts,
    }
    return render(request, 'blog_detail.html', context)


# ================== AFFILIATE VIEWS SECTION ==================

def affiliate_dashboard(request):
    """User affiliate dashboard - FIXED VERSION"""
    user = get_user_from_session(request)
    if not user:
        messages.error(request, "Please log in to access the affiliate dashboard.")
        return redirect('login_page')
    
    try:
        affiliate, created = Affiliate.objects.get_or_create(user=user)
        
        # If newly created, ensure it has a referral code
        if created:
            if not affiliate.referral_code:
                affiliate.generate_referral_code()
                affiliate.save()
        
        cash_value = affiliate.coin_balance * 10
        
        # Referral stats
        pending_referrals = affiliate.referrals.filter(status='pending').count()
        approved_referrals = affiliate.referrals.filter(status='approved').count()
        
        referral_stats = {
            'total_referrals': affiliate.total_referrals,
            'total_coins': affiliate.total_coins_earned,
            'pending_coins': pending_referrals * 50,
            'approved_referrals': approved_referrals,
            'coin_balance': affiliate.coin_balance,
        }
        
        # Weekly number
        weekly_number = WeeklyNumber.objects.filter(is_active=True).first()
        
        # Payout history
        payout_history = PayoutRequest.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Recent referrals
        recent_referrals = affiliate.referrals.select_related('referred_user').order_by('-created_at')[:10]
        
        context = {
            'user_referral_link': f"http://127.0.0.1:8000/signup?ref={affiliate.referral_code}",
            'referral_stats': referral_stats,
            'weekly_number': weekly_number,
            'user_id': user.id,
            'cash_value': cash_value,
            'payout_history': payout_history,
            'recent_referrals': recent_referrals,
            'affiliate': affiliate,
        }
        
        return render(request, 'affiliate_dashboard.html', context)
        
    except Exception as e:
        print(f"Error in affiliate_dashboard: {e}")
        messages.error(request, "Error loading affiliate dashboard.")
        return redirect('account')

def request_payout(request):
    """Handle payout requests - FIXED VERSION"""
    user = get_user_from_session(request)
    if not user:
        messages.error(request, "Please log in to request a payout.")
        return redirect('login_page')
        
    if request.method == 'POST':
        try:
            affiliate = Affiliate.objects.get(user=user)
            
            coin_amount = int(request.POST.get('coin_amount', 0))
            payment_method = request.POST.get('payment_method')
            
            # Validation
            if coin_amount < 50:
                messages.error(request, 'Minimum redemption is 50 coins')
                return redirect('affiliate_dashboard')
            
            if coin_amount > affiliate.coin_balance:
                messages.error(request, 'Insufficient coin balance')
                return redirect('affiliate_dashboard')
            
            # Validate payment method details
            if payment_method == 'mpesa':
                mpesa_number = request.POST.get('mpesa_number')
                if not mpesa_number:
                    messages.error(request, 'M-Pesa number is required')
                    return redirect('affiliate_dashboard')
            elif payment_method == 'bank':
                bank_account = request.POST.get('bank_account')
                bank_name = request.POST.get('bank_name')
                if not bank_account or not bank_name:
                    messages.error(request, 'Bank account details are required')
                    return redirect('affiliate_dashboard')
            elif payment_method == 'paypal':
                paypal_email = request.POST.get('paypal_email')
                if not paypal_email:
                    messages.error(request, 'PayPal email is required')
                    return redirect('affiliate_dashboard')
            
            # Create payout request
            payout = PayoutRequest(
                user=user,
                coin_amount=coin_amount,
                payment_method=payment_method
            )
            
            # Set payment details
            if payment_method == 'mpesa':
                payout.mpesa_number = request.POST.get('mpesa_number')
            elif payment_method == 'bank':
                payout.bank_account = request.POST.get('bank_account')
                payout.bank_name = request.POST.get('bank_name')
            elif payment_method == 'paypal':
                payout.paypal_email = request.POST.get('paypal_email')
            
            payout.save()
            
            # Deduct coins
            affiliate.coin_balance -= coin_amount
            affiliate.save()
            
            messages.success(request, f'Payout request for {coin_amount} coins submitted successfully! You will be paid KES {coin_amount * 10} via {payout.get_payment_method_display()}.')
            
        except Exception as e:
            messages.error(request, f'Error processing payout: {str(e)}')
    
    return redirect('affiliate_dashboard')

def share_referral(request, platform):
    """Handle referral sharing on different platforms - FIXED VERSION"""
    user = get_user_from_session(request)
    if not user:
        messages.error(request, 'Please log in to share your referral link.')
        return redirect('login_page')
    
    try:
        affiliate = Affiliate.objects.get(user=user)
        
        # Generate the actual referral link
        referral_link = f"http://127.0.0.1:8000/signup?ref={affiliate.referral_code}"
        message = f"Join TradeWise using my referral link and get 50 TWC coins! {referral_link}"
        
        share_urls = {
            'whatsapp': f'https://wa.me/?text={message}',
            'facebook': f'https://www.facebook.com/sharer/sharer.php?u={referral_link}',
            'twitter': f'https://twitter.com/intent/tweet?text={message}',
            'telegram': f'https://t.me/share/url?url={referral_link}&text={message}',
        }
        
        share_url = share_urls.get(platform)
        
        if share_url:
            return redirect(share_url)
        else:
            messages.error(request, 'Invalid platform specified.')
            return redirect('affiliate_dashboard')
            
    except Exception as e:
        print(f"Error in share_referral: {e}")
        messages.error(request, 'Error generating share link.')
        return redirect('affiliate_dashboard')


# ================== ADMIN AUTHENTICATION SECTION ==================

def admin_login(request):
    """Admin login"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None and user.is_staff:
                login(request, user)
                
                # Log admin login
                create_admin_log(
                    admin_user=user,
                    action='login',
                    model_name='Authentication',
                    description='Admin logged in successfully',
                    request=request
                )
                
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next', 'admin_dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid credentials or insufficient permissions.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'admin_login.html', {
        'form': form,
        'site_header': 'TradeWise Admin Login'
    })

@login_required
def admin_logout(request):
    """Admin logout"""
    if request.user.is_staff:
        # Log admin logout
        create_admin_log(
            admin_user=request.user,
            action='logout',
            model_name='Authentication',
            description='Admin logged out',
            request=request
        )
        
        logout(request)
        messages.success(request, 'You have been successfully logged out from admin panel.')
        return redirect('admin_login')
    else:
        messages.error(request, 'Access denied.')
        return redirect('index')


# ================== AJAX ENDPOINTS SECTION ==================

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def user_details_ajax(request, user_id):
    """AJAX endpoint for user details"""
    if request.method == 'GET':
        try:
            user = Tradeviewusers.objects.get(id=user_id)
            user_data = {
                'id': user.id,
                'full_name': f"{user.first_name} {user.second_name}",
                'email': user.email,
                'phone': user.phone,
                'account_number': user.account_number,
                'is_active': user.is_active,
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
                'date_joined': user.created_at.strftime('%Y-%m-%d'),
                'email_verified': getattr(user, 'is_email_verified', False),
            }
            return JsonResponse(user_data)
        except Tradeviewusers.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def review_details_ajax(request, review_id):
    """AJAX endpoint for review details"""
    try:
        review = Testimonial.objects.get(id=review_id)
        
        # Build image HTML
        if review.image and hasattr(review.image, 'url'):
            image_html = f'<img src="{review.image.url}" alt="{review.author_name}" class="rounded-circle" style="width: 100px; height: 100px; object-fit: cover;">'
        else:
            image_html = '''
            <div class="no-avatar bg-secondary rounded-circle d-flex align-items-center justify-content-center mx-auto" 
                 style="width: 100px; height: 100px;">
                <i class="fas fa-user text-white fa-3x"></i>
            </div>
            '''
        
        # Build status badges
        status_badge = '<span class="badge badge-success">Approved</span>' if review.is_approved else '<span class="badge badge-warning">Pending Approval</span>'
        featured_badge = '<span class="badge badge-warning">Featured</span>' if review.is_featured else '<span class="badge badge-secondary">Regular</span>'
        
        # Build stars
        stars = '★' * review.rating + '☆' * (5 - review.rating)
        
        html = f"""
        <div class="review-details">
            <div class="text-center mb-4">
                {image_html}
                <h4 class="mt-3">{review.author_name}</h4>
                <p class="text-muted">{review.user_role}</p>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong><i class="fas fa-envelope"></i> Email:</strong><br>
                    {review.email or 'Not provided'}
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-star"></i> Rating:</strong><br>
                    <div class="star-rating-display">
                        {stars} ({review.rating}/5)
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                <strong><i class="fas fa-comment"></i> Review:</strong>
                <p class="mt-2 p-3 bg-light rounded">{review.content}</p>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong><i class="fas fa-calendar"></i> Submitted:</strong><br>
                    {review.created_at.strftime('%B %d, %Y at %H:%M')}
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-sync"></i> Last Updated:</strong><br>
                    {review.updated_at.strftime('%B %d, %Y at %H:%M')}
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <strong>Status:</strong><br>
                    {status_badge}
                </div>
                <div class="col-md-6">
                    <strong>Featured:</strong><br>
                    {featured_badge}
                </div>
            </div>
        </div>
        """
        
        return JsonResponse({'html': html})
        
    except Testimonial.DoesNotExist:
        return JsonResponse({'error': 'Review not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Unable to load review details'}, status=500)


# ================== BLOG AJAX ENDPOINTS ==================

@csrf_exempt
def get_blog_posts_ajax(request):
    """AJAX endpoint to get blog posts for frontend"""
    try:
        posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')[:6]
        
        posts_data = []
        for post in posts:
            post_data = {
                'id': post.id,
                'title': post.title,
                'excerpt': post.excerpt or post.content[:100] + '...' if len(post.content) > 100 else post.content,
                'content': post.content,
                'image_url': post.image.url if post.image and hasattr(post.image, 'url') else '/static/images/blog-placeholder.jpg',
                'author': post.author,
                'created_at': post.created_at.strftime('%B %d, %Y'),
                'slug': post.slug,
            }
            posts_data.append(post_data)
        
        return JsonResponse({
            'success': True,
            'posts': posts_data,
            'count': len(posts_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'posts': []
        })

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def blog_post_details_ajax(request, post_id):
    """AJAX endpoint for blog post details"""
    try:
        post = BlogPost.objects.get(id=post_id)
        
        html = f"""
        <div class="blog-post-details">
            <div class="text-center mb-4">
                {"<img src='" + post.image.url + "' alt='" + post.title + "' class='img-fluid rounded' style='max-height: 300px; width: 100%; object-fit: cover;'>" if post.image and hasattr(post.image, 'url') else ""}
                <h3 class="mt-3">{post.title}</h3>
                <p class="text-muted">By {post.author} | {post.created_at.strftime('%B %d, %Y at %H:%M')}</p>
            </div>
            
            <div class="mb-4">
                <strong>Status:</strong>
                {"<span class='badge badge-success'>Published</span>" if post.is_published else "<span class='badge badge-warning'>Draft</span>"}
            </div>
            
            <div class="mb-4">
                <strong>Excerpt:</strong>
                <p class="mt-2 p-3 bg-light rounded">{post.excerpt or 'No excerpt provided'}</p>
            </div>
            
            <div class="mb-4">
                <strong>Content Preview:</strong>
                <div class="mt-2 p-3 bg-light rounded" style="max-height: 200px; overflow-y: auto;">
                    {post.content[:500] + '...' if len(post.content) > 500 else post.content}
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <strong>Created:</strong><br>
                    {post.created_at.strftime('%B %d, %Y at %H:%M')}
                </div>
                <div class="col-md-6">
                    <strong>Last Updated:</strong><br>
                    {post.updated_at.strftime('%B %d, %Y at %H:%M')}
                </div>
            </div>
        </div>
        """
        
        return JsonResponse({'html': html})
        
    except BlogPost.DoesNotExist:
        return JsonResponse({'error': 'Blog post not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Unable to load blog post details'}, status=500)


# ================== PAYMENT VIEWS SECTION ==================

@csrf_exempt
def mpesa_checkout(request):
    """MPesa checkout for classes"""
    phone = request.POST.get('phone')
    amount = request.session.get('amount', 0) * 100

    cleaned_phone = phone.strip().replace(" ", "").replace("-", "")
    if cleaned_phone.startswith("0"):
        phone = "254" + cleaned_phone[1:]
    else:
        phone = cleaned_phone

    if not phone:
        return redirect('index')

    request.session['phone'] = phone
    ClassesPayment.objects.create(phone=phone, amount=amount)

    try:
        # Simulate payment processing
        return render(request, "loading.html", {"message": "Complete payment on your phone."})
    except Exception as e:
        print("Payment error:", e)
        return render(request, "index.html", {"error": "Payment failed. Try again later."})

@csrf_exempt
def mpesa_checkouts(request):
    """MPesa checkout for merchandise"""
    phone = request.POST.get('phone')
    amount = request.session.get('amount', 0) * 100
    merchid = request.session.get('merch_id')

    cleaned_phone = phone.strip().replace(" ", "").replace("-", "")
    if cleaned_phone.startswith("0"):
        phone = "254" + cleaned_phone[1:]
    else:
        phone = cleaned_phone

    if not phone:
        return redirect('index')

    request.session['phone'] = phone
    MerchPayment.objects.create(phone=phone, amount=amount, merchid=merchid)

    try:
        # Simulate payment processing
        return render(request, "loading.html", {"message": "Complete payment on your phone."})
    except Exception as e:
        print("Payment error:", e)
        return render(request, "index.html", {"error": "Payment failed. Try again later."})

def loading(request):
    """Loading page for payments"""
    return render(request, "loading.html")


# ================== NEWSLETTER SUBSCRIPTION SECTION ==================

@csrf_exempt
def subscribe_newsletter(request):
    """Handle newsletter subscription"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if email:
            try:
                subscriber, created = NewsletterSubscriber.objects.get_or_create(
                    email=email,
                    defaults={'is_active': True}
                )
                
                if created:
                    messages.success(request, 'Thank you for subscribing to our newsletter!')
                else:
                    if not subscriber.is_active:
                        subscriber.is_active = True
                        subscriber.unsubscribed_at = None
                        subscriber.save()
                        messages.success(request, 'Welcome back! You have been resubscribed to our newsletter.')
                    else:
                        messages.info(request, 'You are already subscribed to our newsletter.')
                
            except Exception as e:
                messages.error(request, 'An error occurred. Please try again.')
        else:
            messages.error(request, 'Please enter a valid email address.')
    
    return redirect('index')

@csrf_exempt
def unsubscribe_newsletter(request, email):
    """Handle newsletter unsubscription"""
    try:
        subscriber = NewsletterSubscriber.objects.get(email=email)
        subscriber.is_active = False
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save()
        messages.success(request, 'You have been unsubscribed from our newsletter.')
    except NewsletterSubscriber.DoesNotExist:
        messages.error(request, 'Email address not found in our subscription list.')
    
    return redirect('index')


# ================== API ENDPOINTS SECTION ==================

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def admin_get_dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    today = timezone.now().date()
    
    total_revenue_commitments = ServiceRevenue.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    stats = {
        'total_users': Tradeviewusers.objects.count(),
        'total_revenue': float(total_revenue_commitments),
        'pending_requests': (
            ConsultationRequest.objects.filter(status='pending').count() + 
            CoachingRequest.objects.filter(status='pending').count() +
            GeneralServiceRequest.objects.filter(status='pending').count()
        ),
        'active_traders': Tradeviewusers.objects.count(),
        'total_strategies': Strategy.objects.count(),
        'total_signals': Signal.objects.count(),
        'total_classes': Coaching.objects.count(),
        'new_users_today': Tradeviewusers.objects.filter(created_at__date=today).count(),
        'revenue_today': float(ServiceRevenue.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0),
    }
    return JsonResponse(stats)

@csrf_exempt
def get_reviews_for_frontend(request):
    """API endpoint to get approved reviews for frontend display"""
    try:
        reviews = Testimonial.objects.filter(
            is_approved=True,
            is_active=True
        ).order_by('-is_featured', '-created_at')[:6]
        
        reviews_data = []
        total_rating = 0
        review_count = reviews.count()
        
        for review in reviews:
            try:
                if review.image and hasattr(review.image, 'url'):
                    image_url = review.image.url
                else:
                    image_url = '/static/images/default-avatar.jpg'
            except:
                image_url = '/static/images/default-avatar.jpg'
            
            review_data = {
                'id': review.id,
                'author_name': review.author_name,
                'user_role': review.user_role,
                'content': review.content,
                'rating': review.rating,
                'image_url': image_url,
                'is_featured': review.is_featured,
                'created_at': review.created_at.strftime('%b %d, %Y')
            }
            
            reviews_data.append(review_data)
            total_rating += review.rating
        
        average_rating = total_rating / review_count if review_count > 0 else 0
        
        response_data = {
            'success': True,
            'reviews': reviews_data,
            'average_rating': round(average_rating, 1),
            'total_reviews': review_count
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'reviews': [],
            'average_rating': 0,
            'total_reviews': 0,
            'error': 'Unable to load reviews'
        })


# ================== PAYSTACK PAYMENT VIEWS SECTION ==================

def pricing_plans(request):
    """Display pricing plans"""
    plans = PricingPlan.objects.all().order_by('price')
    return render(request, 'pricing.html', {'plans': plans})

def initialize_plan_payment(request, plan_id):
    """Initialize Paystack payment for a plan"""
    plan = get_object_or_404(PricingPlan, id=plan_id)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Please provide a valid email address')
            return redirect('pricing_plans')
        
        # Generate unique reference
        reference = f"TRD{str(uuid.uuid4())[:8].upper()}"
        
        # Create transaction record - FIXED: Using PaymentTransaction instead of Transaction
        transaction = PaymentTransaction.objects.create(
            email=email,
            amount=plan.price,
            plan=plan,
            reference=reference,
            status='pending'
        )
        
        # Initialize Paystack payment
        paystack = PaystackService()
        callback_url = request.build_absolute_uri(f'/payment/verify/{reference}/')
        
        response = paystack.initialize_transaction(
            email=email,
            amount=plan.price,
            reference=reference,
            callback_url=callback_url,
            metadata={
                'plan_id': plan.id,
                'plan_name': plan.name,
                'custom_fields': [
                    {
                        'display_name': "Plan",
                        'variable_name': "plan",
                        'value': plan.name
                    }
                ]
            }
        )
        
        if response.get('status'):
            transaction.paystack_access_code = response['data']['access_code']
            transaction.save()
            
            # Show loading page before redirecting to Paystack
            return render(request, 'payment_loading.html', {
                'authorization_url': response['data']['authorization_url'],
                'plan': plan,
                'transaction': transaction
            })
        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, response.get('message', 'Payment initialization failed'))
            return redirect('pricing_plans')
    
    # If GET request, show payment form
    return render(request, 'payment_form.html', {
        'plan': plan,
        'paystack_public_key': getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
    })

def verify_payment(request, reference):
    """Verify Paystack payment"""
    # FIXED: Using PaymentTransaction instead of Transaction
    transaction = get_object_or_404(PaymentTransaction, reference=reference)
    
    paystack = PaystackService()
    response = paystack.verify_transaction(reference)
    
    if response.get('status') and response['data']['status'] == 'success':
        transaction.status = 'success'
        transaction.save()
        
        # Here you can add logic to grant user access to the plan
        # For example: create user subscription, send welcome email, etc.
        
        return render(request, 'payment_success.html', {
            'transaction': transaction,
            'plan': transaction.plan
        })
    else:
        transaction.status = 'failed'
        transaction.save()
        return render(request, 'payment_failed.html', {
            'transaction': transaction,
            'plan': transaction.plan,
            'error': response.get('message', 'Payment verification failed')
        })

@csrf_exempt
def paystack_webhook(request):
    """Handle Paystack webhook notifications"""
    if request.method == 'POST':
        payload = json.loads(request.body)
        event = payload.get('event')
        
        if event == 'charge.success':
            reference = payload['data']['reference']
            
            try:
                # FIXED: Using PaymentTransaction instead of Transaction
                transaction = PaymentTransaction.objects.get(reference=reference)
                transaction.status = 'success'
                transaction.save()
                
                # Add your post-payment logic here
                print(f"Payment successful for transaction: {reference}")
                
            except PaymentTransaction.DoesNotExist:
                print(f"Transaction not found: {reference}")
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

def payment_success(request):
    """Payment success page"""
    return render(request, 'payment_success.html')

def payment_failed(request):
    """Payment failed page"""
    return render(request, 'payment_failed.html')


def initialize_plan_payment(request, plan_id):
    """Initialize Paystack payment for a plan - WITH AUTO-CREATION"""
    try:
        plan = PricingPlan.objects.get(id=plan_id)
    except PricingPlan.DoesNotExist:
        # Auto-create pricing plans if they don't exist
        plans_data = {
            1: {'name': 'Starter Package', 'price': 5999.00, 'description': 'Perfect for beginners', 'features': 'Basic Strategies,Email Support,Community Access'},
            2: {'name': 'Professional Package', 'price': 14999.00, 'description': 'For serious traders', 'features': 'Advanced Strategies,Priority Support,1-on-1 Coaching'},
            3: {'name': 'Enterprise Package', 'price': 29999.00, 'description': 'For professional traders', 'features': 'All Features,Dedicated Account Manager,Custom Strategies'},
        }
        
        if plan_id in plans_data:
            plan_data = plans_data[plan_id]
            plan = PricingPlan.objects.create(
                id=plan_id,
                name=plan_data['name'],
                price=plan_data['price'],
                description=plan_data['description'],
                features=plan_data['features'],
                is_active=True
            )
        else:
            messages.error(request, 'Invalid plan selected.')
            return redirect('index')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Please provide a valid email address')
            return redirect('pricing_plans')
        
        # Generate unique reference
        reference = f"TRD{str(uuid.uuid4())[:8].upper()}"
        
        # Create transaction record
        transaction = PaymentTransaction.objects.create(
            email=email,
            amount=plan.price,
            plan=plan,
            reference=reference,
            status='pending'
        )
        
        # Initialize Paystack payment
        paystack = PaystackService()
        callback_url = request.build_absolute_uri(f'/payment/verify/{reference}/')
        
        response = paystack.initialize_transaction(
            email=email,
            amount=plan.price,
            reference=reference,
            callback_url=callback_url,
            metadata={
                'plan_id': plan.id,
                'plan_name': plan.name,
                'custom_fields': [
                    {
                        'display_name': "Plan",
                        'variable_name': "plan",
                        'value': plan.name
                    }
                ]
            }
        )
        
        if response.get('status'):
            transaction.paystack_access_code = response['data']['access_code']
            transaction.save()
            
            # Show loading page before redirecting to Paystack
            return render(request, 'payment_loading.html', {
                'authorization_url': response['data']['authorization_url'],
                'plan': plan,
                'transaction': transaction
            })
        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, response.get('message', 'Payment initialization failed'))
            return redirect('pricing_plans')
    
    # If GET request, show payment form
    return render(request, 'payment_form.html', {
        'plan': plan,
        'paystack_public_key': getattr(settings, 'PAYSTACK_PUBLIC_KEY', '')
    })

def pricing_plans(request):
    """Display pricing plans - WITH AUTO-CREATION"""
    # Check if plans exist, if not create them
    if not PricingPlan.objects.exists():
        plans_data = [
            {'id': 1, 'name': 'Starter Package', 'price': 5999.00, 'description': 'Perfect for beginners', 'features': 'Basic Strategies,Email Support,Community Access'},
            {'id': 2, 'name': 'Professional Package', 'price': 14999.00, 'description': 'For serious traders', 'features': 'Advanced Strategies,Priority Support,1-on-1 Coaching'},
            {'id': 3, 'name': 'Enterprise Package', 'price': 29999.00, 'description': 'For professional traders', 'features': 'All Features,Dedicated Account Manager,Custom Strategies'},
        ]
        
        for plan_data in plans_data:
            PricingPlan.objects.create(**plan_data)
    
    plans = PricingPlan.objects.filter(is_active=True).order_by('price')
    return render(request, 'pricing.html', {'plans': plans})


# ================== LIVE DATA AJAX VIEWS SECTION ==================

@method_decorator(csrf_exempt, name='dispatch')
class LiveRevenueData(View):
    """AJAX view for live revenue data"""
    def get(self, request):
        try:
            # Get revenue data for the last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            revenues = ServiceRevenue.objects.filter(
                created_at__date__range=[start_date, end_date]
            ).order_by('created_at')
            
            dates = []
            amounts = []
            
            # Generate data for the last 30 days
            for i in range(30):
                current_date = start_date + timedelta(days=i)
                daily_revenue = sum([
                    float(revenue.amount) for revenue in revenues 
                    if revenue.created_at.date() == current_date
                ])
                dates.append(current_date.strftime('%m/%d'))
                amounts.append(daily_revenue)
            
            return JsonResponse({
                'success': True,
                'dates': dates,
                'amounts': amounts,
                'total_revenue': sum(amounts)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class RecentActivityData(View):
    """AJAX view for recent activity data"""
    def get(self, request):
        try:
            activities = AdminLog.objects.all().order_by('-timestamp')[:20]
            
            activity_data = []
            for activity in activities:
                activity_data.append({
                    'action': activity.get_action_display(),
                    'description': activity.description,
                    'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M'),
                    'time_ago': self.get_time_ago(activity.timestamp),
                    'admin': activity.admin_user.username,
                    'model': activity.model_name
                })
            
            return JsonResponse({
                'success': True,
                'activities': activity_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'activities': []
            })
    
    def get_time_ago(self, timestamp):
        """Calculate human-readable time ago"""
        now = timezone.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds // 3600 > 0:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds // 60 > 0:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"

@method_decorator(csrf_exempt, name='dispatch')
class QuickStatsData(View):
    """AJAX view for quick stats data"""
    def get(self, request):
        try:
            today = timezone.now().date()
            
            total_users = Tradeviewusers.objects.count()
            new_users_today = Tradeviewusers.objects.filter(created_at__date=today).count()
            
            pending_requests = (
                ConsultationRequest.objects.filter(status='pending').count() + 
                CoachingRequest.objects.filter(status='pending').count() +
                GeneralServiceRequest.objects.filter(status='pending').count()
            )
            
            active_traders = Tradeviewusers.objects.filter(is_active=True).count()
            
            total_revenue = float(ServiceRevenue.objects.aggregate(total=Sum('amount'))['total'] or 0)
            revenue_today = float(ServiceRevenue.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0)
            
            return JsonResponse({
                'success': True,
                'total_users': total_users,
                'new_users_today': new_users_today,
                'pending_requests': pending_requests,
                'active_traders': active_traders,
                'total_revenue': total_revenue,
                'revenue_today': revenue_today
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class UsersData(View):
    """AJAX view for users data"""
    def get(self, request):
        try:
            users = Tradeviewusers.objects.all().values(
                'id', 'first_name', 'second_name', 'email', 'phone', 
                'is_active', 'created_at', 'account_number'
            ).order_by('-created_at')
            
            return JsonResponse({
                'success': True,
                'users': list(users)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'users': []
            })

@method_decorator(csrf_exempt, name='dispatch')
class RequestsData(View):
    """AJAX view for requests data"""
    def get(self, request):
        try:
            # Get all types of requests
            service_requests = GeneralServiceRequest.objects.all().values(
                'id', 'name', 'email', 'phone', 'service_type', 'status', 'created_at'
            )
            
            consultation_requests = ConsultationRequest.objects.all().values(
                'id', 'name', 'email', 'phone', 'class_interest', 'status', 'created_at'
            )
            
            coaching_requests = CoachingRequest.objects.all().values(
                'id', 'name', 'email', 'phone', 'class_type', 'status', 'created_at'
            )
            
            # Combine all requests
            all_requests = []
            
            for req in service_requests:
                all_requests.append({
                    'id': req['id'],
                    'type': 'Service',
                    'name': req['name'],
                    'email': req['email'],
                    'phone': req['phone'],
                    'service_type': req['service_type'],
                    'status': req['status'],
                    'created_at': req['created_at'].strftime('%Y-%m-%d %H:%M') if req['created_at'] else ''
                })
            
            for req in consultation_requests:
                all_requests.append({
                    'id': req['id'],
                    'type': 'Consultation',
                    'name': req['name'],
                    'email': req['email'],
                    'phone': req['phone'],
                    'service_type': req['class_interest'],
                    'status': req['status'],
                    'created_at': req['created_at'].strftime('%Y-%m-%d %H:%M') if req['created_at'] else ''
                })
            
            for req in coaching_requests:
                all_requests.append({
                    'id': req['id'],
                    'type': 'Coaching',
                    'name': req['name'],
                    'email': req['email'],
                    'phone': req['phone'],
                    'service_type': req['class_type'],
                    'status': req['status'],
                    'created_at': req['created_at'].strftime('%Y-%m-%d %H:%M') if req['created_at'] else ''
                })
            
            # Sort by creation date
            all_requests.sort(key=lambda x: x['created_at'], reverse=True)
            
            return JsonResponse({
                'success': True,
                'requests': all_requests
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'requests': []
            })


# ================== ERROR HANDLING SECTION ==================

def handle_404(request, exception):
    """Custom 404 error handler"""
    return render(request, '404.html', status=404)

def handle_500(request):
    """Custom 500 error handler"""
    return render(request, '500.html', status=500)

def handle_403(request, exception):
    """Custom 403 error handler"""
    return render(request, '403.html', status=403)

def handle_400(request, exception):
    """Custom 400 error handler"""
    return render(request, '400.html', status=400)


# ================== ALIAS VIEWS FOR URL COMPATIBILITY ==================

def dashboard(request):
    """User dashboard - alias for account page"""
    return account(request)

def admin_dashboard(request):
    """Admin dashboard - alias for admin_dashboard_main"""
    return admin_dashboard_main(request)


# ================== AJAX QUICK STATS VIEW ==================

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_quick_stats(request):
    """AJAX endpoint for quick admin dashboard statistics"""
    try:
        today = timezone.now().date()
        
        # User statistics
        total_users = Tradeviewusers.objects.count()
        new_users_today = Tradeviewusers.objects.filter(created_at__date=today).count()
        active_users = Tradeviewusers.objects.filter(is_active=True).count()
        
        # Revenue statistics
        total_revenue = float(ServiceRevenue.objects.aggregate(total=Sum('amount'))['total'] or 0)
        revenue_today = float(ServiceRevenue.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0)
        
        # Request statistics
        pending_consultations = ConsultationRequest.objects.filter(status='pending').count()
        pending_classes = CoachingRequest.objects.filter(status='pending').count()
        pending_services = GeneralServiceRequest.objects.filter(status='pending').count()
        pending_requests_count = pending_consultations + pending_classes + pending_services
        
        # Content statistics
        total_strategies = Strategy.objects.count()
        total_signals = Signal.objects.count()
        total_classes = TradingClass.objects.count()
        total_blog_posts = BlogPost.objects.count()
        
        # Affiliate statistics
        total_affiliates = Affiliate.objects.count()
        pending_payouts = PayoutRequest.objects.filter(status='pending').count()
        
        stats = {
            'success': True,
            'users': {
                'total': total_users,
                'new_today': new_users_today,
                'active': active_users,
            },
            'revenue': {
                'total': total_revenue,
                'today': revenue_today,
            },
            'requests': {
                'pending': pending_requests_count,
                'consultations': pending_consultations,
                'classes': pending_classes,
                'services': pending_services,
            },
            'content': {
                'strategies': total_strategies,
                'signals': total_signals,
                'classes': total_classes,
                'blog_posts': total_blog_posts,
            },
            'affiliates': {
                'total': total_affiliates,
                'pending_payouts': pending_payouts,
            },
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return JsonResponse(stats)
        
    except Exception as e:
        print(f"❌ Error in ajax_quick_stats: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'users': {'total': 0, 'new_today': 0, 'active': 0},
            'revenue': {'total': 0, 'today': 0},
            'requests': {'pending': 0, 'consultations': 0, 'classes': 0, 'services': 0},
            'content': {'strategies': 0, 'signals': 0, 'classes': 0, 'blog_posts': 0},
            'affiliates': {'total': 0, 'pending_payouts': 0},
        })


# ================== MISSING AJAX VIEW FUNCTIONS ==================

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_merchandise_data(request):
    """AJAX endpoint for merchandise data"""
    try:
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        search = request.GET.get('search', '')
        category = request.GET.get('category', '')
        
        # Base queryset
        merchandise = Merchandise.objects.all()
        
        # Apply search filter
        if search:
            merchandise = merchandise.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )
        
        # Apply category filter
        if category:
            merchandise = merchandise.filter(category=category)
        
        # Order by creation date
        merchandise = merchandise.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(merchandise, per_page)
        try:
            merchandise_page = paginator.page(page)
        except PageNotAnInteger:
            merchandise_page = paginator.page(1)
        except EmptyPage:
            merchandise_page = paginator.page(paginator.num_pages)
        
        # Prepare data for response
        merchandise_data = []
        for item in merchandise_page:
            merchandise_data.append({
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'category_display': item.get_category_display(),
                'description': item.description,
                'price': item.price,
                'is_active': item.is_active,
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M'),
                'image_url': item.image.url if item.image and hasattr(item.image, 'url') else '/static/images/merchandise-placeholder.jpg',
            })
        
        return JsonResponse({
            'success': True,
            'merchandise': merchandise_data,
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_merchandise': paginator.count,
                'has_previous': merchandise_page.has_previous(),
                'has_next': merchandise_page.has_next(),
            },
            'stats': {
                'total_merchandise': merchandise.count(),
                'active_merchandise': merchandise.filter(is_active=True).count(),
                'categories_count': merchandise.values('category').distinct().count(),
                'total_value': sum(item.price for item in merchandise),
            }
        })
        
    except Exception as e:
        print(f"❌ Error in ajax_merchandise_data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'merchandise': [],
            'pagination': {
                'current_page': 1,
                'total_pages': 1,
                'total_merchandise': 0,
                'has_previous': False,
                'has_next': False,
            },
            'stats': {
                'total_merchandise': 0,
                'active_merchandise': 0,
                'categories_count': 0,
                'total_value': 0,
            }
        })

@csrf_exempt
def ajax_market_strategies(request):
    """AJAX endpoint for market strategies"""
    try:
        strategies = Strategy.objects.filter(is_active=True).order_by('-created_at')
        
        strategies_data = []
        for strategy in strategies:
            strategies_data.append({
                'id': strategy.id,
                'title': strategy.title,
                'description': strategy.description,
                'price_usd': float(strategy.price_usd),
                'price_kes': float(strategy.price_kes),
                'image_url': strategy.image.url if strategy.image and hasattr(strategy.image, 'url') else '/static/images/strategy-placeholder.jpg',
                'created_at': strategy.created_at.strftime('%B %d, %Y'),
                'stats': strategy.stats or {},
            })
        
        return JsonResponse({
            'success': True,
            'strategies': strategies_data,
            'count': len(strategies_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'strategies': [],
            'count': 0
        })

@csrf_exempt
def ajax_market_signals(request):
    """AJAX endpoint for market signals"""
    try:
        signals = Signal.objects.filter(is_active=True).order_by('-created_at')
        
        signals_data = []
        for signal in signals:
            signals_data.append({
                'id': signal.id,
                'title': signal.title,
                'description': signal.description,
                'price_usd': float(signal.price_usd),
                'price_kes': float(signal.price_kes),
                'image_url': signal.image.url if signal.image and hasattr(signal.image, 'url') else '/static/images/signal-placeholder.jpg',
                'accuracy_forex': signal.accuracy_forex,
                'accuracy_crypto': signal.accuracy_crypto,
                'created_at': signal.created_at.strftime('%B %d, %Y'),
                'success_rate': ((signal.accuracy_forex + signal.accuracy_crypto) / 2) if signal.accuracy_forex and signal.accuracy_crypto else 0,
            })
        
        return JsonResponse({
            'success': True,
            'signals': signals_data,
            'count': len(signals_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'signals': [],
            'count': 0
        })

@csrf_exempt
def ajax_market_software(request):
    """AJAX endpoint for market software"""
    try:
        software_list = Software.objects.filter(is_active=True).order_by('-created_at')
        
        software_data = []
        for software in software_list:
            software_data.append({
                'id': software.id,
                'name': software.name,
                'description': software.description,
                'version': software.version,
                'file_type': software.file_type,
                'file_type_display': software.get_file_type_display(),
                'download_count': software.download_count,
                'thumbnail_url': software.thumbnail.url if software.thumbnail and hasattr(software.thumbnail, 'url') else '/static/images/software-placeholder.jpg',
                'created_at': software.created_at.strftime('%B %d, %Y'),
                'file_url': software.file.url if software.file and hasattr(software.file, 'url') else '#',
            })
        
        return JsonResponse({
            'success': True,
            'software': software_data,
            'count': len(software_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'software': [],
            'count': 0
        })

@csrf_exempt
def ajax_software_details(request, id):
    """AJAX endpoint for software details"""
    try:
        software = Software.objects.get(id=id)
        
        html = f"""
        <div class="software-details">
            <div class="text-center mb-4">
                {"<img src='" + software.thumbnail.url + "' alt='" + software.name + "' class='img-fluid rounded' style='max-height: 200px;'>" if software.thumbnail and hasattr(software.thumbnail, 'url') else ""}
                <h3 class="mt-3">{software.name}</h3>
                <p class="text-muted">Version {software.version} • {software.get_file_type_display()}</p>
            </div>
            
            <div class="mb-4">
                <strong>Description:</strong>
                <p class="mt-2 p-3 bg-light rounded">{software.description}</p>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6">
                    <strong><i class="fas fa-download"></i> Downloads:</strong><br>
                    {software.download_count}
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-calendar"></i> Released:</strong><br>
                    {software.created_at.strftime('%B %d, %Y')}
                </div>
            </div>
            
            <div class="mb-4">
                <strong>File Type:</strong><br>
                <span class="badge badge-primary">{software.get_file_type_display()}</span>
            </div>
            
            {"<div class='text-center'><a href='" + software.file.url + "' class='btn btn-primary btn-lg' download><i class='fas fa-download'></i> Download Now</a></div>" if software.file and hasattr(software.file, 'url') else "<div class='alert alert-warning text-center'>File not available</div>"}
        </div>
        """
        
        return JsonResponse({'html': html})
        
    except Software.DoesNotExist:
        return JsonResponse({'error': 'Software not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Unable to load software details'}, status=500)

@csrf_exempt
def track_download(request, id):
    """Track software downloads"""
    try:
        software = Software.objects.get(id=id)
        software.download_count += 1
        software.save()
        
        return JsonResponse({
            'success': True,
            'download_count': software.download_count,
            'message': 'Download tracked successfully'
        })
        
    except Software.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Software not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def submit_review(request):
    """Handle review submissions from frontend"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            user_role = request.POST.get('user_role', 'Trader')
            rating = request.POST.get('rating')
            review_text = request.POST.get('review_text', '').strip()
            avatar = request.FILES.get('avatar')
            
            if not name or not review_text or not rating:
                return JsonResponse({
                    'success': False,
                    'message': 'Name, review text, and rating are required.'
                })
            
            review = Testimonial.objects.create(
                author_name=name,
                email=email if email else None,
                user_role=user_role,
                rating=int(rating),
                content=review_text,
                image=avatar,
                is_approved=False,  # New reviews need admin approval
                is_featured=False,
                from_admin=False,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your review! It will be published after approval.',
                'review_id': review.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error submitting review: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def payout_details_ajax(request, payout_id):
    """AJAX endpoint for payout details"""
    try:
        payout = PayoutRequest.objects.get(id=payout_id)
        
        html = f"""
        <div class="payout-details">
            <div class="text-center mb-4">
                <h4>Payout Request #{payout.id}</h4>
                <p class="text-muted">Submitted: {payout.created_at.strftime('%B %d, %Y at %H:%M')}</p>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong><i class="fas fa-user"></i> User:</strong><br>
                    {payout.user.first_name} {payout.user.second_name}
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-envelope"></i> Email:</strong><br>
                    {payout.user.email}
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong><i class="fas fa-coins"></i> Coin Amount:</strong><br>
                    {payout.coin_amount} coins
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-money-bill-wave"></i> Cash Value:</strong><br>
                    KES {payout.amount_kes}
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong><i class="fas fa-wallet"></i> Payment Method:</strong><br>
                    {payout.get_payment_method_display()}
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-info-circle"></i> Status:</strong><br>
                    <span class="badge badge-{'warning' if payout.status == 'pending' else 'success' if payout.status == 'approved' else 'danger'}">
                        {payout.get_status_display()}
                    </span>
                </div>
            </div>
            
            <div class="mb-3">
                <strong><i class="fas fa-credit-card"></i> Payment Details:</strong><br>
                {payout.payment_details_display}
            </div>
            
            {"<div class='mb-3'><strong><i class='fas fa-sticky-note'></i> Admin Notes:</strong><br>" + payout.admin_notes + "</div>" if payout.admin_notes else ""}
            
            {"<div class='mb-3'><strong><i class='fas fa-user-cog'></i> Processed By:</strong><br>" + payout.processed_by.username + " on " + payout.processed_at.strftime('%B %d, %Y at %H:%M') + "</div>" if payout.processed_by else ""}
        </div>
        """
        
        return JsonResponse({'html': html})
        
    except PayoutRequest.DoesNotExist:
        return JsonResponse({'error': 'Payout request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Unable to load payout details'}, status=500)

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def affiliate_details_ajax(request, user_id):
    """AJAX endpoint for affiliate details"""
    try:
        user = Tradeviewusers.objects.get(id=user_id)
        affiliate = Affiliate.objects.get(user=user)
        
        # Get referral stats
        referrals = affiliate.referrals.select_related('referred_user').order_by('-created_at')
        pending_referrals = referrals.filter(status='pending')
        approved_referrals = referrals.filter(status='approved')
        
        html = f"""
        <div class="affiliate-details">
            <div class="text-center mb-4">
                <h4>Affiliate Profile</h4>
                <p class="text-muted">{user.first_name} {user.second_name}</p>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong><i class="fas fa-user"></i> Affiliate Name:</strong><br>
                    {user.first_name} {user.second_name}
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-envelope"></i> Email:</strong><br>
                    {user.email}
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong><i class="fas fa-code"></i> Referral Code:</strong><br>
                    <code>{affiliate.referral_code}</code>
                </div>
                <div class="col-md-6">
                    <strong><i class="fas fa-link"></i> Referral Link:</strong><br>
                    <small>{affiliate.referral_link}</small>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-3 text-center">
                    <div class="card bg-primary text-white">
                        <div class="card-body">
                            <h4>{affiliate.total_referrals}</h4>
                            <small>Total Referrals</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 text-center">
                    <div class="card bg-success text-white">
                        <div class="card-body">
                            <h4>{affiliate.total_coins_earned}</h4>
                            <small>Total Coins</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 text-center">
                    <div class="card bg-info text-white">
                        <div class="card-body">
                            <h4>{affiliate.coin_balance}</h4>
                            <small>Coin Balance</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 text-center">
                    <div class="card bg-warning text-white">
                        <div class="card-body">
                            <h4>KES {affiliate.total_payouts}</h4>
                            <small>Total Payouts</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mb-3">
                <strong><i class="fas fa-users"></i> Referral Breakdown:</strong>
                <ul class="list-group mt-2">
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        Approved Referrals
                        <span class="badge badge-success badge-pill">{approved_referrals.count()}</span>
                    </li>
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        Pending Referrals
                        <span class="badge badge-warning badge-pill">{pending_referrals.count()}</span>
                    </li>
                </ul>
            </div>
            
            <div class="mb-3">
                <strong><i class="fas fa-history"></i> Recent Referrals:</strong>
                <div class="mt-2" style="max-height: 200px; overflow-y: auto;">
                    {"".join([f'<div class="alert alert-sm alert-{"success" if ref.status == "approved" else "warning"} mb-1">{ref.referred_user.email} - {ref.created_at.strftime("%Y-%m-%d")}</div>' for ref in referrals[:5]])}
                </div>
            </div>
        </div>
        """
        
        return JsonResponse({'html': html})
        
    except (Tradeviewusers.DoesNotExist, Affiliate.DoesNotExist):
        return JsonResponse({'error': 'Affiliate not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Unable to load affiliate details'}, status=500)

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def debug_reviews(request):
    """Debug endpoint for reviews"""
    try:
        reviews = Testimonial.objects.all().order_by('-created_at')
        
        debug_data = {
            'total_reviews': reviews.count(),
            'approved_reviews': reviews.filter(is_approved=True).count(),
            'pending_reviews': reviews.filter(is_approved=False).count(),
            'featured_reviews': reviews.filter(is_featured=True).count(),
            'reviews': list(reviews.values('id', 'author_name', 'is_approved', 'is_featured', 'created_at'))
        }
        
        return JsonResponse(debug_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)})

# ================== CARDDATA VIEWS.PY ==================
def ajax_card_data(request):
    """AJAX endpoint for comprehensive card data with statistics"""
    try:
        # Get the TradeWise card data
        card = get_or_create_tradewise_card()
        
        # Get additional statistics
        today = timezone.now().date()
        total_users = Tradeviewusers.objects.count()
        new_users_today = Tradeviewusers.objects.filter(created_at__date=today).count()
        total_revenue = float(ServiceRevenue.objects.aggregate(total=Sum('amount'))['total'] or 0)
        
        card_data = {
            'success': True,
            'card': {
                'card_number': card.card_number,
                'capital_available': card.capital_available,
                'partner_name': card.partner_name,
                'contact_number': card.contact_number,
                'title': card.title,
                'description': card.description,
                'price_monthly': float(card.price_monthly),
                'price_yearly': float(card.price_yearly),
                'status': card.status,
                'image_url': card.image.url if card.image and hasattr(card.image, 'url') else '',
            },
            'statistics': {
                'total_users': total_users,
                'new_users_today': new_users_today,
                'total_revenue': total_revenue,
                'active_traders': total_users,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        return JsonResponse(card_data)
        
    except Exception as e:
        print(f"❌ Error in ajax_card_data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'card': {
                'card_number': '6734 559',
                'capital_available': '$500,000',
                'partner_name': 'SPALIS FX',
                'contact_number': '+254742962615',
                'title': 'TradeWise Premium',
                'description': 'Access premium trading features and exclusive content',
                'price_monthly': 49.99,
                'price_yearly': 499.99,
                'status': 'active',
                'image_url': '',
            },
            'statistics': {
                'total_users': 0,
                'new_users_today': 0,
                'total_revenue': 0,
                'active_traders': 0,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    


# ================== MISSING AJAX VIEW FUNCTIONS ==================

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_revenue_data(request):
    """AJAX endpoint for revenue data with charts"""
    try:
        # Get revenue data for the last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        revenues = ServiceRevenue.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).order_by('created_at')
        
        # Generate daily revenue data
        dates = []
        daily_amounts = []
        
        for i in range(30):
            current_date = start_date + timedelta(days=i)
            daily_revenue = sum([
                float(revenue.amount) for revenue in revenues 
                if revenue.created_at.date() == current_date
            ])
            dates.append(current_date.strftime('%m/%d'))
            daily_amounts.append(daily_revenue)
        
        # Calculate cumulative revenue
        cumulative_amounts = []
        cumulative_total = 0
        for amount in daily_amounts:
            cumulative_total += amount
            cumulative_amounts.append(cumulative_total)
        
        # Service type breakdown
        service_types = {}
        for revenue in revenues:
            service_type = revenue.service_type
            if service_type not in service_types:
                service_types[service_type] = 0
            service_types[service_type] += float(revenue.amount)
        
        # Prepare response data
        revenue_data = {
            'success': True,
            'daily_data': {
                'dates': dates,
                'amounts': daily_amounts,
            },
            'cumulative_data': {
                'dates': dates,
                'amounts': cumulative_amounts,
            },
            'service_breakdown': {
                'labels': list(service_types.keys()),
                'data': list(service_types.values()),
            },
            'summary': {
                'total_revenue': sum(daily_amounts),
                'average_daily': sum(daily_amounts) / len(daily_amounts) if daily_amounts else 0,
                'max_daily': max(daily_amounts) if daily_amounts else 0,
                'revenue_today': daily_amounts[-1] if daily_amounts else 0,
            }
        }
        
        return JsonResponse(revenue_data)
        
    except Exception as e:
        print(f"❌ Error in ajax_revenue_data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'daily_data': {'dates': [], 'amounts': []},
            'cumulative_data': {'dates': [], 'amounts': []},
            'service_breakdown': {'labels': [], 'data': []},
            'summary': {
                'total_revenue': 0,
                'average_daily': 0,
                'max_daily': 0,
                'revenue_today': 0,
            }
        })

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_user_analytics(request):
    """AJAX endpoint for user analytics data"""
    try:
        # User growth over last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        user_data = []
        dates = []
        
        for i in range(30):
            current_date = start_date + timedelta(days=i)
            users_count = Tradeviewusers.objects.filter(
                created_at__date__lte=current_date
            ).count()
            user_data.append(users_count)
            dates.append(current_date.strftime('%m/%d'))
        
        # User activity data (last 7 days)
        active_users_7_days = []
        active_dates = []
        
        for i in range(7):
            current_date = end_date - timedelta(days=(6-i))
            # This is a simplified active user count - you might want to track actual logins
            active_count = Tradeviewusers.objects.filter(
                last_login__date=current_date
            ).count()
            active_users_7_days.append(active_count)
            active_dates.append(current_date.strftime('%a'))
        
        # User demographics
        total_users = Tradeviewusers.objects.count()
        active_users = Tradeviewusers.objects.filter(is_active=True).count()
        verified_users = Tradeviewusers.objects.filter(is_email_verified=True).count()
        new_users_today = Tradeviewusers.objects.filter(created_at__date=end_date).count()
        
        analytics_data = {
            'success': True,
            'user_growth': {
                'dates': dates,
                'counts': user_data,
            },
            'user_activity': {
                'dates': active_dates,
                'counts': active_users_7_days,
            },
            'demographics': {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users,
                'new_users_today': new_users_today,
                'inactive_users': total_users - active_users,
                'unverified_users': total_users - verified_users,
            },
            'growth_rates': {
                'daily_growth': new_users_today,
                'weekly_growth': Tradeviewusers.objects.filter(
                    created_at__date__range=[end_date - timedelta(days=7), end_date]
                ).count(),
                'monthly_growth': Tradeviewusers.objects.filter(
                    created_at__date__range=[start_date, end_date]
                ).count(),
            }
        }
        
        return JsonResponse(analytics_data)
        
    except Exception as e:
        print(f"❌ Error in ajax_user_analytics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'user_growth': {'dates': [], 'counts': []},
            'user_activity': {'dates': [], 'counts': []},
            'demographics': {
                'total_users': 0,
                'active_users': 0,
                'verified_users': 0,
                'new_users_today': 0,
                'inactive_users': 0,
                'unverified_users': 0,
            },
            'growth_rates': {
                'daily_growth': 0,
                'weekly_growth': 0,
                'monthly_growth': 0,
            }
        })

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_service_metrics(request):
    """AJAX endpoint for service performance metrics"""
    try:
        # Service request statistics
        total_service_requests = GeneralServiceRequest.objects.count()
        pending_services = GeneralServiceRequest.objects.filter(status='pending').count()
        completed_services = GeneralServiceRequest.objects.filter(status='completed').count()
        
        # Consultation statistics
        total_consultations = ConsultationRequest.objects.count()
        pending_consultations = ConsultationRequest.objects.filter(status='pending').count()
        
        # Coaching statistics
        total_coaching = CoachingRequest.objects.count()
        pending_coaching = CoachingRequest.objects.filter(status='pending').count()
        
        # Revenue by service type
        service_revenues = ServiceRevenue.objects.values('service_type').annotate(
            total_revenue=Sum('amount'),
            request_count=Count('id')
        )
        
        service_breakdown = []
        for revenue in service_revenues:
            service_breakdown.append({
                'service_type': revenue['service_type'],
                'total_revenue': float(revenue['total_revenue'] or 0),
                'request_count': revenue['request_count']
            })
        
        # Monthly performance
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        monthly_revenue = ServiceRevenue.objects.filter(
            created_at__month=current_month,
            created_at__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_requests = GeneralServiceRequest.objects.filter(
            created_at__month=current_month,
            created_at__year=current_year
        ).count()
        
        metrics_data = {
            'success': True,
            'request_stats': {
                'total_services': total_service_requests,
                'pending_services': pending_services,
                'completed_services': completed_services,
                'total_consultations': total_consultations,
                'pending_consultations': pending_consultations,
                'total_coaching': total_coaching,
                'pending_coaching': pending_coaching,
            },
            'service_breakdown': service_breakdown,
            'monthly_performance': {
                'revenue': float(monthly_revenue),
                'requests': monthly_requests,
                'completion_rate': (completed_services / total_service_requests * 100) if total_service_requests > 0 else 0,
            },
            'efficiency_metrics': {
                'avg_response_time': 24,  # hours - you might want to calculate this
                'completion_rate': (completed_services / total_service_requests * 100) if total_service_requests > 0 else 0,
                'customer_satisfaction': 95,  # percentage - you might want to track this
            }
        }
        
        return JsonResponse(metrics_data)
        
    except Exception as e:
        print(f"❌ Error in ajax_service_metrics: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'request_stats': {
                'total_services': 0,
                'pending_services': 0,
                'completed_services': 0,
                'total_consultations': 0,
                'pending_consultations': 0,
                'total_coaching': 0,
                'pending_coaching': 0,
            },
            'service_breakdown': [],
            'monthly_performance': {
                'revenue': 0,
                'requests': 0,
                'completion_rate': 0,
            },
            'efficiency_metrics': {
                'avg_response_time': 0,
                'completion_rate': 0,
                'customer_satisfaction': 0,
            }
        })

@csrf_exempt
def ajax_live_updates(request):
    """AJAX endpoint for live dashboard updates"""
    try:
        # Real-time data updates
        current_time = timezone.now()
        
        # Recent activities
        recent_activities = AdminLog.objects.all().order_by('-timestamp')[:5]
        
        activities_data = []
        for activity in recent_activities:
            activities_data.append({
                'action': activity.get_action_display(),
                'description': activity.description,
                'timestamp': activity.timestamp.strftime('%H:%M:%S'),
                'admin': activity.admin_user.username,
            })
        
        # Real-time counts
        online_users = Tradeviewusers.objects.filter(
            last_login__gte=current_time - timedelta(minutes=30)
        ).count()
        
        pending_transactions = PaymentTransaction.objects.filter(
            status='pending'
        ).count()
        
        # System status
        system_status = {
            'database': 'online',
            'payments': 'online',
            'email': 'online',
            'api': 'online',
        }
        
        live_data = {
            'success': True,
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'activities': activities_data,
            'real_time_counts': {
                'online_users': online_users,
                'pending_transactions': pending_transactions,
                'active_sessions': request.session.get('active_sessions', 0),
            },
            'system_status': system_status,
            'notifications': {
                'unread_count': Notification.objects.filter(is_read=False).count(),
                'urgent_alerts': 0,  # You can implement urgent alert logic
            }
        }
        
        return JsonResponse(live_data)
        
    except Exception as e:
        print(f"❌ Error in ajax_live_updates: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'activities': [],
            'real_time_counts': {
                'online_users': 0,
                'pending_transactions': 0,
                'active_sessions': 0,
            },
            'system_status': {
                'database': 'offline',
                'payments': 'offline',
                'email': 'offline',
                'api': 'offline',
            },
            'notifications': {
                'unread_count': 0,
                'urgent_alerts': 0,
            }
        })




@csrf_exempt
def ajax_general_stats(request):
    """General AJAX endpoint for various statistics"""
    try:
        # Comprehensive statistics
        total_users = Tradeviewusers.objects.count()
        total_revenue = float(ServiceRevenue.objects.aggregate(total=Sum('amount'))['total'] or 0)
        total_affiliates = Affiliate.objects.count()
        total_blog_posts = BlogPost.objects.count()
        
        # Today's statistics
        today = timezone.now().date()
        new_users_today = Tradeviewusers.objects.filter(created_at__date=today).count()
        revenue_today = float(ServiceRevenue.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0)
        
        # Pending items
        pending_requests = (
            GeneralServiceRequest.objects.filter(status='pending').count() +
            ConsultationRequest.objects.filter(status='pending').count() +
            CoachingRequest.objects.filter(status='pending').count()
        )
        
        pending_reviews = Testimonial.objects.filter(is_approved=False).count()
        pending_payouts = PayoutRequest.objects.filter(status='pending').count()
        
        stats_data = {
            'success': True,
            'totals': {
                'users': total_users,
                'revenue': total_revenue,
                'affiliates': total_affiliates,
                'blog_posts': total_blog_posts,
            },
            'today': {
                'new_users': new_users_today,
                'revenue': revenue_today,
            },
            'pending': {
                'requests': pending_requests,
                'reviews': pending_reviews,
                'payouts': pending_payouts,
            },
            'rates': {
                'conversion_rate': 15.5,  # You can calculate this
                'growth_rate': 8.2,       # You can calculate this
                'completion_rate': 92.7,  # You can calculate this
            }
        }
        
        return JsonResponse(stats_data)
        
    except Exception as e:
        print(f"❌ Error in ajax_general_stats: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'totals': {'users': 0, 'revenue': 0, 'affiliates': 0, 'blog_posts': 0},
            'today': {'new_users': 0, 'revenue': 0},
            'pending': {'requests': 0, 'reviews': 0, 'payouts': 0},
            'rates': {'conversion_rate': 0, 'growth_rate': 0, 'completion_rate': 0},
        })



@csrf_exempt
def ajax_dashboard_widgets(request):
    """AJAX endpoint for dashboard widget data"""
    try:
        # Quick stats for dashboard widgets
        today = timezone.now().date()
        
        # User widget
        total_users = Tradeviewusers.objects.count()
        new_users_today = Tradeviewusers.objects.filter(created_at__date=today).count()
        user_growth = (new_users_today / total_users * 100) if total_users > 0 else 0
        
        # Revenue widget
        total_revenue = float(ServiceRevenue.objects.aggregate(total=Sum('amount'))['total'] or 0)
        revenue_today = float(ServiceRevenue.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0)
        revenue_growth = (revenue_today / total_revenue * 100) if total_revenue > 0 else 0
        
        # Requests widget
        pending_requests = (
            GeneralServiceRequest.objects.filter(status='pending').count() +
            ConsultationRequest.objects.filter(status='pending').count() +
            CoachingRequest.objects.filter(status='pending').count()
        )
        total_requests = (
            GeneralServiceRequest.objects.count() +
            ConsultationRequest.objects.count() +
            CoachingRequest.objects.count()
        )
        completion_rate = ((total_requests - pending_requests) / total_requests * 100) if total_requests > 0 else 0
        
        # Affiliate widget
        total_affiliates = Affiliate.objects.count()
        pending_payouts = PayoutRequest.objects.filter(status='pending').count()
        total_payouts = PayoutRequest.objects.filter(status='approved').aggregate(total=Sum('amount_kes'))['total_kes__sum'] or 0
        
        widget_data = {
            'success': True,
            'widgets': {
                'users': {
                    'total': total_users,
                    'today': new_users_today,
                    'growth': user_growth,
                    'trend': 'up' if new_users_today > 0 else 'down',
                },
                'revenue': {
                    'total': total_revenue,
                    'today': revenue_today,
                    'growth': revenue_growth,
                    'trend': 'up' if revenue_today > 0 else 'down',
                },
                'requests': {
                    'pending': pending_requests,
                    'completion_rate': completion_rate,
                    'trend': 'up' if completion_rate > 50 else 'down',
                },
                'affiliates': {
                    'total': total_affiliates,
                    'pending_payouts': pending_payouts,
                    'total_payouts': float(total_payouts),
                    'trend': 'up' if total_affiliates > 0 else 'down',
                },
            },
            'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return JsonResponse(widget_data)
        
    except Exception as e:
        print(f"❌ Error in ajax_dashboard_widgets: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'widgets': {
                'users': {'total': 0, 'today': 0, 'growth': 0, 'trend': 'down'},
                'revenue': {'total': 0, 'today': 0, 'growth': 0, 'trend': 'down'},
                'requests': {'pending': 0, 'completion_rate': 0, 'trend': 'down'},
                'affiliates': {'total': 0, 'pending_payouts': 0, 'total_payouts': 0, 'trend': 'down'},
            }
        })                    




# ================== MISSING AJAX VIEW FUNCTIONS ==================

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_activity_data(request):
    """AJAX endpoint for activity data"""
    try:
        # Get recent admin activities
        activities = AdminLog.objects.all().order_by('-timestamp')[:20]
        
        activity_data = []
        for activity in activities:
            activity_data.append({
                'id': activity.id,
                'admin_user': activity.admin_user.username,
                'action': activity.get_action_display(),
                'model_name': activity.model_name,
                'description': activity.description,
                'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': get_time_ago(activity.timestamp),
                'ip_address': activity.ip_address or 'N/A',
                'object_id': activity.object_id or 'N/A',
            })
        
        return JsonResponse({
            'success': True,
            'activities': activity_data,
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"❌ Error in ajax_activity_data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'activities': [],
        })

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_users_data(request):
    """AJAX endpoint for users data"""
    try:
        users = Tradeviewusers.objects.all().values(
            'id', 'first_name', 'second_name', 'email', 'phone', 
            'is_active', 'created_at', 'account_number', 'last_login'
        ).order_by('-created_at')
        
        return JsonResponse({
            'success': True,
            'users': list(users)
        })
        
    except Exception as e:
        print(f"❌ Error in ajax_users_data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'users': []
        })

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_requests_data(request):
    """AJAX endpoint for requests data"""
    try:
        # Get all types of requests
        service_requests = GeneralServiceRequest.objects.all().values(
            'id', 'name', 'email', 'phone', 'service_type', 'status', 'created_at'
        )
        
        consultation_requests = ConsultationRequest.objects.all().values(
            'id', 'name', 'email', 'phone', 'class_interest', 'status', 'created_at'
        )
        
        coaching_requests = CoachingRequest.objects.all().values(
            'id', 'name', 'email', 'phone', 'class_type', 'status', 'created_at'
        )
        
        # Combine all requests
        all_requests = []
        
        for req in service_requests:
            all_requests.append({
                'id': req['id'],
                'type': 'Service',
                'name': req['name'],
                'email': req['email'],
                'phone': req['phone'],
                'service_type': req['service_type'],
                'status': req['status'],
                'created_at': req['created_at'].strftime('%Y-%m-%d %H:%M') if req['created_at'] else ''
            })
        
        for req in consultation_requests:
            all_requests.append({
                'id': req['id'],
                'type': 'Consultation',
                'name': req['name'],
                'email': req['email'],
                'phone': req['phone'],
                'service_type': req['class_interest'],
                'status': req['status'],
                'created_at': req['created_at'].strftime('%Y-%m-%d %H:%M') if req['created_at'] else ''
            })
        
        for req in coaching_requests:
            all_requests.append({
                'id': req['id'],
                'type': 'Coaching',
                'name': req['name'],
                'email': req['email'],
                'phone': req['phone'],
                'service_type': req['class_type'],
                'status': req['status'],
                'created_at': req['created_at'].strftime('%Y-%m-%d %H:%M') if req['created_at'] else ''
            })
        
        # Sort by creation date
        all_requests.sort(key=lambda x: x['created_at'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'requests': all_requests
        })
        
    except Exception as e:
        print(f"❌ Error in ajax_requests_data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'requests': []
        })

# ================== UTILITY FUNCTION FOR TIME FORMATTING ==================

def get_time_ago(timestamp):
    """Calculate human-readable time ago"""
    now = timezone.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds // 3600 > 0:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds // 60 > 0:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def index(request):
    """Home page view WITH BLOG POSTS"""
    try:
        analysis = ForexAnalysis.objects.all().order_by('-created_at')
        tradewise_card = get_or_create_tradewise_card()
        tradewise_coin = get_or_create_tradewise_coin()

        # Merchandise data
        all_categories = ['caps-hats', 'hoodies', 't-shirts', 'accessories']
        
        category_items = {}
        for category in all_categories:
            try:
                item = Merchandise.objects.filter(category=category, is_active=True).first()
                category_items[category] = item
            except:
                category_items[category] = None
        
        # Testimonials
        testimonials = Testimonial.objects.filter(is_active=True, is_featured=True)[:5]
        
        # Trading classes
        trading_classes = TradingClass.objects.filter(is_active=True)[:4]
        
        # BLOG POSTS
        blog_posts = get_blog_posts_for_frontend()
        
        context = {
            'analysis': analysis,
            'tradewise_coin': tradewise_coin,
            'tradewise_card': tradewise_card,
            'all_categories': all_categories,
            'category_items': category_items,
            'testimonials': testimonials,
            'trading_classes': trading_classes,
            'blog_posts': blog_posts,
        }
        return render(request, "index.html", context)
    except Exception as e:
        print(f"❌ Error in index view: {e}")
        # Fallback context if there are errors
        context = {
            'analysis': [],
            'tradewise_coin': get_or_create_tradewise_coin(),
            'tradewise_card': get_or_create_tradewise_card(),
            'all_categories': ['caps-hats', 'hoodies', 't-shirts', 'accessories'],
            'category_items': {},
            'testimonials': [],
            'trading_classes': [],
            'blog_posts': [],
        }
        return render(request, "index.html", context)




def signup(request):
    """User registration - FIXED VERSION with better error handling"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        second_name = request.POST.get('second_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        referral_code = request.POST.get('referral_code')

        print(f"🔐 SIGNUP ATTEMPT: {first_name} {second_name}, Email: {email}, Phone: {phone}")

        # Validate required fields
        if not all([first_name, second_name, email, password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'login.html')

        # Validate password strength
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'login.html')

        # Check if email already exists
        if Tradeviewusers.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered.')
            return render(request, 'login.html')

        try:
            # Create user with phone field
            user = Tradeviewusers.objects.create(
                first_name=first_name.strip(),
                second_name=second_name.strip(),
                email=email.strip().lower(),
                password=password,
                phone=phone.strip() if phone else None
            )
            
            print(f"✅ USER CREATED: {user.account_number}, {user.email}")

            # Handle referral - FIXED with better error handling
            if referral_code:
                try:
                    referrer_affiliate = Affiliate.objects.get(referral_code=referral_code.strip())
                    Referral.objects.create(
                        referrer=referrer_affiliate,
                        referred_user=user,
                        coins_earned=50,
                        status='pending'
                    )
                    messages.info(request, 'Referral applied! You will receive coins once your account is verified.')
                    print(f"✅ REFERRAL APPLIED: {referral_code}")
                except Affiliate.DoesNotExist:
                    messages.warning(request, 'Invalid referral code.')
                    print("❌ INVALID REFERRAL CODE")
                except Exception as e:
                    print(f"⚠️ Referral error (non-critical): {e}")
            
            # Send verification email
            email_sent = user.send_verification_email()
            print(f"✅ VERIFICATION EMAIL SENT: {email_sent}")

            # Send admin notification
            admin_notified = send_admin_notification(user)
            print(f"✅ ADMIN NOTIFIED: {admin_notified}")

            # Send welcome email
            welcome_sent = user.send_welcome_email(password)
            print(f"✅ WELCOME EMAIL SENT: {welcome_sent}")

            if email_sent:
                messages.success(request, 'Account created successfully! Please check your email to verify your account.')
            else:
                messages.warning(request, 'Account created successfully! But we could not send verification email. Please contact support.')
            
            return redirect('login_page')
            
        except Exception as e:
            print(f"❌ SIGNUP ERROR: {e}")
            # More specific error message
            if 'UNIQUE constraint' in str(e):
                messages.error(request, 'Account creation issue. Please try again or contact support.')
            else:
                messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'login.html')

    return render(request, 'login.html')

    # ================== CARD VIEWS.PY ==================

def ajax_card_data(request):
    """AJAX endpoint for card data - RETURNS HTML"""
    try:
        # Get the TradeWise card data
        card = get_or_create_tradewise_card()
        
        # Render the card HTML template
        html_content = f"""
        <!-- Designed Card -->
        <div id="designedCard" class="membership-card" style="background: linear-gradient(145deg, #1a2a4f 0%, #0d1a33 100%); border-radius: 20px; padding: 30px; box-shadow: 0 15px 40px rgba(0,0,0,0.2); position: relative; overflow: hidden; color: white; max-width: 500px; margin: 0 auto;">
            <!-- Card Watermark -->
            <div style="position: absolute; top: -30px; right: -30px; opacity: 0.1; font-size: 12rem; font-weight: 700; color: white; transform: rotate(15deg);">TRADE</div>
            
            <!-- Card Content -->
            <div class="card-content" style="position: relative; z-index: 2;">
                <!-- Logo -->
                <div class="mb-4" style="display: flex; align-items: center;">
                    <div style="height: 50px; width: 150px; background: rgba(255,255,255,0.2); border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-right: 15px;">
                        <span style="color: white; font-weight: bold;">TRADEWISE</span>
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 600;">The Wisest Choice</div>
                </div>
                
                <!-- Card Number -->
                <div class="mb-4" style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 10px;">
                    <div style="font-size: 0.9rem; margin-bottom: 5px; opacity: 0.8;">TRADEWISE CARD</div>
                    <div style="font-size: 1.5rem; letter-spacing: 3px; font-weight: 600;">
                        {card.card_number}
                    </div>
                </div>
                
                <!-- Capital Available -->
                <div class="mb-4">
                    <div style="font-size: 0.9rem; opacity: 0.8;">CAPITAL AVAILABLE</div>
                    <div style="font-size: 2rem; font-weight: 700;">
                        {card.capital_available}
                    </div>
                </div>
                
                <!-- Partner Info -->
                <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                    <div>
                        <div style="font-size: 0.9rem; opacity: 0.8;">PARTNER</div>
                        <div style="font-size: 1.2rem; font-weight: 600;">
                            {card.partner_name}
                        </div>
                    </div>
                    <div>
                        <div style="font-size: 0.9rem; opacity: 0.8;">CONTACT</div>
                        <div style="font-size: 1.2rem; font-weight: 600;">
                            {card.contact_number}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Real Card Image (hidden by default) -->
        <div id="realCard" style="display: none; text-align: center;">
            <div style="background: linear-gradient(145deg, #2c3e50 0%, #3498db 100%); border-radius: 20px; padding: 40px; color: white; max-width: 500px; margin: 0 auto;">
                <h3 style="margin-bottom: 20px;">Physical Card</h3>
                <p>Your physical TradeWise membership card</p>
                <div style="font-size: 3rem; margin: 20px 0;">💳</div>
                <p style="font-size: 0.9rem; opacity: 0.8;">Contact support to receive your physical card</p>
            </div>
        </div>
        
        <!-- Toggle Button -->
        <div style="text-align: center; margin-top: 30px;">
            <button id="toggleCardBtn" onclick="toggleCardView()" style="background: linear-gradient(135deg, #3498db, #2c3e50); color: white; border: none; border-radius: 30px; padding: 12px 30px; font-weight: 600; cursor: pointer; box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3); transition: all 0.3s ease;">
                <span id="btnText">Show Physical Card</span>
                <i id="btnIcon" class="fas fa-eye" style="margin-left: 8px;"></i>
            </button>
        </div>
        """
        
        return JsonResponse({
            'success': True,
            'html': html_content
        })
        
    except Exception as e:
        print(f"❌ Error in ajax_card_data: {e}")
        # Return fallback HTML on error
        return JsonResponse({
            'success': False,
            'html': """
            <div style="text-align: center; padding: 40px; background: #f8f9fa; border-radius: 10px;">
                <h3>Card Loading Error</h3>
                <p>Unable to load card data. Please try again.</p>
                <button onclick="loadCardData()" class="btn btn-primary">Retry</button>
            </div>
            """
        })
    

# ================== REVENUE DATA ==================    
@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_revenue_data(request):
    """AJAX endpoint for revenue data with charts - FIXED VERSION"""
    try:
        # Get revenue data for the last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Generate sample data for testing
        dates = []
        daily_amounts = []
        
        for i in range(30):
            current_date = start_date + timedelta(days=i)
            dates.append(current_date.strftime('%m/%d'))
            # Generate realistic sample data
            daily_amounts.append(random.randint(5000, 25000))
        
        # Calculate cumulative revenue
        cumulative_amounts = []
        cumulative_total = 0
        for amount in daily_amounts:
            cumulative_total += amount
            cumulative_amounts.append(cumulative_total)
        
        # Service type breakdown (sample data)
        service_types = {
            'Strategies': 45000,
            'Signals': 32000,
            'Classes': 28000,
            'Consultation': 15000,
        }
        
        # Prepare response data
        revenue_data = {
            'success': True,
            'daily_data': {
                'dates': dates,
                'amounts': daily_amounts,
            },
            'cumulative_data': {
                'dates': dates,
                'amounts': cumulative_amounts,
            },
            'service_breakdown': {
                'labels': list(service_types.keys()),
                'data': list(service_types.values()),
            },
            'summary': {
                'total_revenue': sum(daily_amounts),
                'average_daily': sum(daily_amounts) / len(daily_amounts),
                'max_daily': max(daily_amounts),
                'revenue_today': daily_amounts[-1],
            }
        }
        
        print(f"✅ Revenue data generated: {len(daily_amounts)} days, total: {sum(daily_amounts)}")
        return JsonResponse(revenue_data)
        
    except Exception as e:
        print(f"❌ Error in ajax_revenue_data: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'daily_data': {'dates': [], 'amounts': []},
            'cumulative_data': {'dates': [], 'amounts': []},
            'service_breakdown': {'labels': [], 'data': []},
            'summary': {
                'total_revenue': 0,
                'average_daily': 0,
                'max_daily': 0,
                'revenue_today': 0,
            }
        })
# ================== ACTIVITY DATA ==================  

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_quick_stats(request):
    """AJAX endpoint for quick admin dashboard statistics - FIXED VERSION"""
    try:
        today = timezone.now().date()
        
        # User statistics
        total_users = Tradeviewusers.objects.count()
        new_users_today = Tradeviewusers.objects.filter(created_at__date=today).count()
        active_users = Tradeviewusers.objects.filter(is_active=True).count()
        
        # Revenue statistics - use actual data from ServiceRevenue
        total_revenue = float(ServiceRevenue.objects.aggregate(total=Sum('amount'))['total'] or 0)
        revenue_today = float(ServiceRevenue.objects.filter(created_at__date=today).aggregate(total=Sum('amount'))['total'] or 0)
        
        # Request statistics
        pending_consultations = ConsultationRequest.objects.filter(status='pending').count()
        pending_classes = CoachingRequest.objects.filter(status='pending').count()
        pending_services = GeneralServiceRequest.objects.filter(status='pending').count()
        pending_requests_count = pending_consultations + pending_classes + pending_services
        
        stats = {
            'success': True,
            'total_users': total_users,
            'new_users_today': new_users_today,
            'active_users': active_users,
            'total_revenue': total_revenue,
            'revenue_today': revenue_today,
            'pending_requests': pending_requests_count,
            'pending_consultations': pending_consultations,
            'pending_classes': pending_classes,
            'pending_services': pending_services,
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ Quick stats: {total_users} users, KES {total_revenue} revenue, {pending_requests_count} pending requests")
        return JsonResponse(stats)
        
    except Exception as e:
        print(f"❌ Error in ajax_quick_stats: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'total_users': 0,
            'new_users_today': 0,
            'active_users': 0,
            'total_revenue': 0,
            'revenue_today': 0,
            'pending_requests': 0,
            'pending_consultations': 0,
            'pending_classes': 0,
            'pending_services': 0,
        })
# ================== REVENUE DATA ==================  
@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def ajax_activity_data(request):
    """AJAX endpoint for activity data - FIXED VERSION"""
    try:
        # Get recent admin activities
        activities = AdminLog.objects.all().order_by('-timestamp')[:20]
        
        activity_data = []
        for activity in activities:
            activity_data.append({
                'id': activity.id,
                'admin_user': activity.admin_user.username if activity.admin_user else 'System',
                'action': activity.get_action_display(),
                'model_name': activity.model_name,
                'description': activity.description,
                'timestamp': activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'time_ago': get_time_ago(activity.timestamp),
                'ip_address': activity.ip_address or 'N/A',
                'object_id': activity.object_id or 'N/A',
            })
        
        return JsonResponse({
            'success': True,
            'activities': activity_data,
            'total_count': len(activity_data),
            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        print(f"❌ Error in ajax_activity_data: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'activities': [],
            'total_count': 0
        })

def get_time_ago(timestamp):
    """Calculate human-readable time ago"""
    now = timezone.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds // 3600 > 0:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds // 60 > 0:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"
    

  
# ================== STANDALONE BLOG VIEWS ==================

def blog_home(request):
    """Main blog page with all published posts"""
    try:
        # Get all published blog posts
        blog_posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
        
        # Pagination
        paginator = Paginator(blog_posts, 9)  # 9 posts per page
        page = request.GET.get('page')
        
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)
        
        context = {
            'blog_posts': posts,
            'total_posts': blog_posts.count(),
        }
        return render(request, 'blog.html', context)
        
    except Exception as e:
        print(f"❌ Blog home error: {e}")
        context = {
            'blog_posts': [],
            'total_posts': 0,
        }
        return render(request, 'blog.html', context)

def blog_detail(request, id):
    """Individual blog post detail page"""
    try:
        post = get_object_or_404(BlogPost, id=id, is_published=True)
        
        # Get related posts (exclude current post)
        related_posts = BlogPost.objects.filter(
            is_published=True
        ).exclude(id=post.id).order_by('-created_at')[:3]
        
        context = {
            'post': post,
            'related_posts': related_posts,
        }
        return render(request, 'blog_detail.html', context)
        
    except Exception as e:
        print(f"❌ Blog detail error: {e}")
        messages.error(request, 'Blog post not found.')
        return redirect('blog_home')

def blog_posts_ajax(request):
    """AJAX endpoint for blog posts (for homepage)"""
    try:
        posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')[:6]
        
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'excerpt': post.excerpt or post.content[:150] + '...',
                'content': post.content,
                'image_url': post.image.url if post.image and hasattr(post.image, 'url') else '/static/images/blog-placeholder.jpg',
                'author': post.author or 'TradeWise Team',
                'created_at': post.created_at.strftime('%B %d, %Y'),
                'read_time': f"{max(1, len(post.content) // 500)} min read",
            })
        
        return JsonResponse({
            'success': True,
            'posts': posts_data,
            'count': len(posts_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'posts': []
        })

def create_blog_post(request):
    """Create a new blog post (for admin)"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('index')
    
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
            excerpt = request.POST.get('excerpt', '')
            image = request.FILES.get('image')
            is_published = request.POST.get('is_published') == 'on'
            
            if not title or not content:
                messages.error(request, 'Title and content are required.')
                return redirect('admin_dashboard')
            
            blog_post = BlogPost.objects.create(
                title=title,
                content=content,
                excerpt=excerpt,
                image=image,
                is_published=is_published,
                author=request.user.username,
                status='published' if is_published else 'draft'
            )
            
            messages.success(request, f'Blog post "{title}" created successfully!')
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating blog post: {str(e)}')
            return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')

def blog_debug(request):
    """Debug endpoint to check blog posts"""
    try:
        all_posts = BlogPost.objects.all()
        published_posts = BlogPost.objects.filter(is_published=True)
        
        debug_info = {
            'success': True,
            'total_posts': all_posts.count(),
            'published_posts': published_posts.count(),
            'all_posts': list(all_posts.values('id', 'title', 'is_published', 'created_at', 'author')),
            'published_posts_list': list(published_posts.values('id', 'title', 'is_published', 'created_at')),
        }
        
        return JsonResponse(debug_info)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    

 # ================== INDEPENDENT MERCHANDISE VIEWS ==================

def merchandise_home(request):
    """Standalone merchandise homepage"""
    try:
        all_categories = ['caps-hats', 'hoodies', 't-shirts', 'accessories']
        
        # Get merchandise data
        category_items = {}
        category_items_grid = {}
        
        for category in all_categories:
            # Get first item for thumbnail
            item = Merchandise.objects.filter(category=category, is_active=True).first()
            category_items[category] = item
            
            # Get all items for grid
            items = Merchandise.objects.filter(category=category, is_active=True)[:8]
            category_items_grid[category] = items
        
        context = {
            'all_categories': all_categories,
            'category_items': category_items,
            'category_items_grid': category_items_grid,
        }
        return render(request, 'merchandise/merch_home.html', context)
        
    except Exception as e:
        print(f"❌ Merchandise home error: {e}")
        context = {
            'all_categories': ['caps-hats', 'hoodies', 't-shirts', 'accessories'],
            'category_items': {},
            'category_items_grid': {},
        }
        return render(request, 'merchandise/merch_home.html', context)

def merchandise_category(request, category):
    """Merchandise by category"""
    try:
        items = Merchandise.objects.filter(category=category, is_active=True).order_by('-created_at')
        category_display = dict(Merchandise.CATEGORY_CHOICES).get(category, "Merchandise")
        
        context = {
            'items': items,
            'category_name': category_display,
            'current_category': category,
        }
        return render(request, 'merchandise/merch_category.html', context)
        
    except Exception as e:
        print(f"❌ Merchandise category error: {e}")
        messages.error(request, 'Error loading category.')
        return redirect('merchandise_home')

@csrf_exempt
def ajax_merchandise_data(request):
    """AJAX endpoint for merchandise data"""
    try:
        all_categories = ['caps-hats', 'hoodies', 't-shirts', 'accessories']
        
        category_data = {}
        for category in all_categories:
            items = Merchandise.objects.filter(category=category, is_active=True)[:8]
            category_data[category] = []
            
            for item in items:
                category_data[category].append({
                    'id': item.id,
                    'name': item.name,
                    'description': item.description,
                    'price': item.price,
                    'image_url': item.image.url if item.image and hasattr(item.image, 'url') else '/static/images/merch-placeholder.jpg',
                    'category': item.category,
                })
        
        return JsonResponse({
            'success': True,
            'categories': category_data,
            'total_items': Merchandise.objects.filter(is_active=True).count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'categories': {}
        })

@csrf_exempt
def process_merchandise_payment(request):
    """Process merchandise payment with M-Pesa"""
    if request.method == 'POST':
        try:
            item_id = request.POST.get('item_id')
            phone = request.POST.get('phone')
            
            # Get merchandise item
            merchandise = get_object_or_404(Merchandise, id=item_id)
            
            # Generate unique reference
            reference = f"MCH{str(uuid.uuid4())[:8].upper()}"
            
            # Create payment record
            payment = MerchPayment.objects.create(
                merchid=merchandise.id,
                phone=phone,
                amount=merchandise.price,
                reference=reference,
                customer_email=request.POST.get('email', ''),
                shipping_address=request.POST.get('address', ''),
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Payment initiated successfully!',
                'reference': reference,
                'amount': merchandise.price
            })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Payment processing error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})   
 

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from .models import Testimonial
import json

# ==================== REVIEWS VIEWS - FIXED VERSION ====================

@csrf_exempt
def submit_review(request):
    """Handle review submissions from frontend - FIXED VERSION"""
    if request.method == 'POST':
        try:
            print("📥 Review submission received")
            print("📦 POST data:", dict(request.POST))
            
            # Get data from form
            author_name = request.POST.get('reviewerName', '').strip()
            email = request.POST.get('reviewerEmail', '').strip()
            user_role = request.POST.get('reviewerRole', 'Trader')
            rating = request.POST.get('rating')
            content = request.POST.get('reviewText', '').strip()
            
            print(f"🔍 Form data: name={author_name}, email={email}, role={user_role}, rating={rating}")
            
            # Validate required fields
            if not author_name:
                return JsonResponse({
                    'success': False, 
                    'message': 'Please enter your name.'
                })
            
            if not content:
                return JsonResponse({
                    'success': False, 
                    'message': 'Please enter your review text.'
                })
            
            if not rating:
                return JsonResponse({
                    'success': False, 
                    'message': 'Please select a rating.'
                })
            
            # Convert rating to integer
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    return JsonResponse({
                        'success': False, 
                        'message': 'Rating must be between 1 and 5.'
                    })
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False, 
                    'message': 'Invalid rating value.'
                })
            
            # Create the review
            review = Review.objects.create(
                author_name=author_name,
                email=email if email else None,
                user_role=user_role,
                rating=rating,
                content=content,
                is_approved=False,  # New reviews need admin approval
                is_featured=False,
                from_admin=False,
                is_active=True
            )
            
            print(f"✅ Review created: ID {review.id}, Author: {author_name}")
            
            # Send success response
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your review! It will be published after approval.',
                'review_id': review.id
            })
            
        except Exception as e:
            print(f"❌ Error in submit_review: {e}")
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'success': False,
                'message': f'Error submitting review: {str(e)}'
            })
    
    return JsonResponse({
        'success': False, 
        'message': 'Invalid request method. Please use POST.'
    })

@csrf_exempt
def reviews_api(request):
    """API endpoint to fetch approved reviews for frontend - FIXED VERSION"""
    if request.method == 'GET':
        try:
            print("📥 Fetching reviews for frontend")
            
            # Get only approved and active reviews for public display
            reviews = Review.objects.filter(
                is_approved=True, 
                is_active=True
            ).order_by('-is_featured', '-created_at')[:6]  # Limit to 6 reviews
            
            # Convert to JSON-serializable format
            reviews_data = []
            total_rating = 0
            review_count = reviews.count()
            
            for review in reviews:
                # Get image URL safely
                try:
                    if review.image and hasattr(review.image, 'url'):
                        image_url = review.image.url
                    else:
                        image_url = '/static/images/default-avatar.jpg'
                except:
                    image_url = '/static/images/default-avatar.jpg'
                
                review_data = {
                    'id': review.id,
                    'author_name': review.author_name,
                    'user_role': review.user_role,
                    'rating': review.rating,
                    'content': review.content,
                    'image_url': image_url,
                    'is_featured': review.is_featured,
                    'created_at': review.created_at.strftime('%b %d, %Y'),
                }
                
                reviews_data.append(review_data)
                total_rating += review.rating
            
            # Calculate average rating
            average_rating = total_rating / review_count if review_count > 0 else 0
            
            print(f"✅ Sent {len(reviews_data)} reviews to frontend")
            
            return JsonResponse({
                'success': True,
                'reviews': reviews_data,
                'statistics': {
                    'total_reviews': review_count,
                    'average_rating': round(average_rating, 1),
                }
            })
            
        except Exception as e:
            print(f"❌ Error in reviews_api: {e}")
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'success': False,
                'error': str(e),
                'reviews': [],
                'statistics': {
                    'total_reviews': 0,
                    'average_rating': 0,
                }
            })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

# ==================== ADMIN REVIEW MANAGEMENT - FIXED VERSION ====================

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def admin_reviews_management(request):
    """Admin reviews management - FIXED VERSION"""
    try:
        # Get all reviews for admin
        reviews = Review.objects.all().order_by('-created_at')
        
        # Calculate statistics
        total_reviews = reviews.count()
        approved_reviews = reviews.filter(is_approved=True).count()
        pending_reviews = reviews.filter(is_approved=False).count()
        featured_reviews = reviews.filter(is_featured=True).count()
        
        # Pagination
        paginator = Paginator(reviews, 10)
        page_number = request.GET.get('reviews_page', 1)
        
        try:
            reviews_page = paginator.page(page_number)
        except PageNotAnInteger:
            reviews_page = paginator.page(1)
        except EmptyPage:
            reviews_page = paginator.page(paginator.num_pages)
        
        context = {
            'reviews': reviews_page,
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'pending_reviews': pending_reviews,
            'featured_reviews': featured_reviews,
        }
        
        return context
        
    except Exception as e:
        print(f"❌ Error in admin_reviews_management: {e}")
        return {
            'reviews': [],
            'total_reviews': 0,
            'approved_reviews': 0,
            'pending_reviews': 0,
            'featured_reviews': 0,
        }

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def approve_review(request, review_id):
    """Approve a review - FIXED VERSION"""
    try:
        review = get_object_or_404(Review, id=review_id)
        review.is_approved = True
        review.save()
        
        messages.success(request, f'Review from {review.author_name} approved!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Review approved'})
            
    except Exception as e:
        print(f"❌ Error approving review: {e}")
        messages.error(request, 'Error approving review.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error approving review'})
    
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def toggle_featured(request, review_id):
    """Toggle featured status - FIXED VERSION"""
    try:
        review = get_object_or_404(Review, id=review_id)
        review.is_featured = not review.is_featured
        review.save()
        
        status = 'featured' if review.is_featured else 'unfeatured'
        messages.success(request, f'Review {status} successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True, 
                'message': f'Review {status}',
                'is_featured': review.is_featured
            })
            
    except Exception as e:
        print(f"❌ Error toggling featured: {e}")
        messages.error(request, 'Error updating review.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error updating review'})
    
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def delete_review(request, review_id):
    """Delete a review - FIXED VERSION"""
    try:
        review = get_object_or_404(Review, id=review_id)
        author_name = review.author_name
        review.delete()
        
        messages.success(request, f'Review from {author_name} deleted!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Review deleted'})
            
    except Exception as e:
        print(f"❌ Error deleting review: {e}")
        messages.error(request, 'Error deleting review.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error deleting review'})
    
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin_user, login_url='/admin/login/')
def add_review_admin(request):
    """Add review from admin - FIXED VERSION"""
    if request.method == 'POST':
        try:
            author_name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            user_role = request.POST.get('user_role', 'Trader')
            rating = request.POST.get('rating')
            content = request.POST.get('review_text', '').strip()
            avatar = request.FILES.get('avatar')
            is_approved = request.POST.get('is_approved') == 'on'
            is_featured = request.POST.get('is_featured') == 'on'
            
            if not author_name or not content or not rating:
                messages.error(request, 'Name, review text, and rating are required.')
                return redirect('admin_dashboard')
            
            review = Review.objects.create(
                author_name=author_name,
                email=email if email else None,
                user_role=user_role,
                rating=int(rating),
                content=content,
                image=avatar,
                is_approved=is_approved,
                is_featured=is_featured,
                from_admin=True,
                is_active=True
            )
            
            messages.success(request, f'Review from {author_name} added successfully!')
            
        except Exception as e:
            print(f"❌ Error adding review: {e}")
            messages.error(request, 'Error adding review.')
    
    return redirect('admin_dashboard')
 
# ================== COMPLETE VIEWS.PY ==================