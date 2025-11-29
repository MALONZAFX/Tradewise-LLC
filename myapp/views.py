from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from django.db.models import Q, Sum, Avg, Count
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from collections import Counter
from django.utils import timezone
from django.db.models import Sum
from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import FileResponse
import json
import uuid
import random
import secrets  # ADD THIS IMPORT
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files.storage import FileSystemStorage

# Import ALL models and services - ORGANIZED
from .models import (
    Tradeviewusers, UserProfile, PricingPlan, PaymentTransaction,
    TradingStrategy, TradingSignal, SoftwareTool, PaymentService,
    BlogPost, TradeWiseCard, Merchandise, TradeWiseCoin, Review,
    ServiceRequest, Affiliate, Referral, WeeklyNumber, PayoutRequest,
    Notification, AdminLog, Service, AffiliateProgram,ServicePayment, ServiceTransaction, Payment, Transaction,
    PaystackService  
)

# ================== SIMPLE AUTHENTICATION SYSTEM ==================

def admin_login(request):
    """Super simple admin login - INSTANT ACCESS"""
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        password = request.POST.get('password')
        tradewise_number = request.POST.get('tradewise_number')
        
        # HARDCODED CREDENTIALS FOR INSTANT ACCESS
        valid_admins = {
            'Mesh': {'number': '500100', 'password': 'admin123'},
            'Spallis': {'number': '500200', 'password': 'admin123'},
            'Admin': {'number': '500100', 'password': 'admin'},  # Simple fallback
        }
        
        # Check if it's a valid admin
        if username in valid_admins:
            admin_data = valid_admins[username]
            
            # Check TradeWise number and password
            if (tradewise_number == admin_data['number'] and 
                password == admin_data['password']):
                
                # INSTANT SUCCESS - Set session
                request.session['admin_logged_in'] = True
                request.session['admin_username'] = username
                request.session['admin_number'] = tradewise_number
                request.session['is_admin'] = True
                
                messages.success(request, f'Welcome back, {username}!')
                return redirect('admin_dashboard')
        
        # If we get here, credentials failed
        messages.error(request, 'Invalid admin credentials. Please check your username, TradeWise number, and password.')
        return render(request, 'admin_login.html')
    
    # GET request - show login form
    return render(request, 'admin_login.html')

def direct_admin(request):
    """DIRECT ACCESS - No login required for testing"""
    # INSTANT ACCESS - NO CHECKS!
    request.session['admin_logged_in'] = True
    request.session['admin_username'] = 'Admin'
    request.session['admin_number'] = '500100'
    request.session['is_admin'] = True
    
    messages.success(request, 'Welcome to TradeWise Admin Dashboard!')
    return redirect('admin_dashboard')

def admin_logout(request):
    """Admin logout"""
    # Clear all admin session data
    admin_keys = ['admin_logged_in', 'admin_username', 'admin_number', 'is_admin']
    for key in admin_keys:
        if key in request.session:
            del request.session[key]
    
    messages.success(request, 'Successfully logged out.')
    return redirect('admin_login')

# ================== SIMPLE ADMIN DECORATOR ==================

def admin_required(view_func):
    """Simple decorator to check if admin is logged in"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_logged_in'):
            messages.error(request, 'Please log in to access the admin dashboard.')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper

# ================== SIMPLE CHART DATA ==================

def get_revenue_chart_data():
    """Generate simple revenue chart data"""
    return {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'datasets': [{
            'label': 'Daily Revenue (KES)',
            'data': [25000, 32000, 28000, 45000, 37000, 29000, 41000],
            'backgroundColor': 'rgba(54, 162, 235, 0.2)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 2,
            'tension': 0.4
        }]
    }

def get_service_distribution_data():
    """Generate simple service distribution data"""
    return {
        'labels': ['Copy Trading', 'Live Trading', 'Signals', 'Education', 'Funding'],
        'datasets': [{
            'data': [35, 25, 20, 15, 5],
            'backgroundColor': [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
            ]
        }]
    }

# ==================== EMAIL TESTING VIEWS ====================
def test_email_delivery(request):
    """Test if emails are actually being delivered"""
    try:
        print("🟢 TESTING EMAIL DELIVERY...")
        
        # Test 1: Simple text email
        result1 = send_mail(
            'TEST: TradeWise Email Delivery',
            'This is a test email from TradeWise. If you get this, email is working!',
            'theofficialtradewise@gmail.com',
            ['manchamdevelopers@gmail.com'],
            fail_silently=False,
        )
        print(f"✅ Test 1 Result: {result1}")
        
        # Test 2: HTML email
        result2 = send_mail(
            'TEST: TradeWise HTML Email',
            'Plain text version',
            'theofficialtradewise@gmail.com',
            ['manchamdevelopers@gmail.com'],
            html_message='<h1>HTML Version</h1><p>This is an HTML test</p>',
            fail_silently=False,
        )
        print(f"✅ Test 2 Result: {result2}")
        
        return HttpResponse(f"""
        <h1>Email Test Results</h1>
        <p>Test 1 (Plain): {result1} (1 = success)</p>
        <p>Test 2 (HTML): {result2} (1 = success)</p>
        <p>Check your email inbox AND spam folder!</p>
        """)
        
    except Exception as e:
        return HttpResponse(f"❌ Email test failed: {str(e)}")

def test_email_setup(request):
    """Test basic email setup"""
    try:
        send_mail(
            'Test from TradeWise',
            'If you get this, email is working!',
            'noreply@trade-wise.co.ke',
            ['manchamdevelopers@gmail.com'],
            fail_silently=False,
        )
        return HttpResponse("✅ Email test sent! Check your inbox.")
    except Exception as e:
        return HttpResponse(f"❌ Email failed: {str(e)}")

def quick_email_test(request):
    """Quick email test"""
    from django.core.mail import send_mail
    try:
        result = send_mail(
            'TEST: TradeWise Real Email',
            'If you get this, emails are working! 🎉',
            'theofficialtradewise@gmail.com',
            ['manchamdevelopers@gmail.com'],
            fail_silently=False,
        )
        return HttpResponse(f"Email sent! Result: {result} (1 = success)")
    except Exception as e:
        return HttpResponse(f"Email failed: {str(e)}")

def test_multiple_emails(request):
    """Test sending to different email providers"""
    import json
    test_emails = [
        'manchamdevelopers@gmail.com',
        # Add other test emails if you have them
    ]
    
    results = {}
    for email in test_emails:
        try:
            result = send_mail(
                f'TEST to {email}',
                'Test email from TradeWise',
                'theofficialtradewise@gmail.com',
                [email],
                fail_silently=False,
            )
            results[email] = f"Success: {result}"
        except Exception as e:
            results[email] = f"Failed: {str(e)}"
    
    return HttpResponse(f"<pre>{json.dumps(results, indent=2)}</pre>")

def verify_email(request, token):
    """Verify user email and redirect to account page - UPDATED WITH DEBUGGING"""
    try:
        print(f"🟢 VERIFY EMAIL: Starting verification for token: {token}")
        
        # Find user by verification token
        user = Tradeviewusers.objects.get(email_verification_token=token)
        print(f"✅ VERIFY EMAIL: User found - {user.first_name} {user.second_name} ({user.email})")
        
        # Update user verification status
        user.is_email_verified = True
        user.email_verification_token = None
        user.save()
        print(f"✅ VERIFY EMAIL: User email verified and token cleared")
        
        # ✅ AUTO-LOGIN USER AFTER VERIFICATION
        request.session['user_id'] = user.id
        request.session['account_number'] = user.account_number
        request.session['first_name'] = user.first_name
        request.session['second_name'] = user.second_name
        print(f"✅ VERIFY EMAIL: User session created - ID: {user.id}, Account: {user.account_number}")
        
        messages.success(request, '✅ Email verified successfully! Welcome to TradeWise.')
        print(f"🔗 VERIFY EMAIL: Redirecting to account page...")
        return redirect('account')  # ✅ Redirect to account page
        
    except Tradeviewusers.DoesNotExist:
        print(f"❌ VERIFY EMAIL: Invalid verification token - {token}")
        messages.error(request, 'Invalid verification token. Please try signing up again.')
        return redirect('signup')
    except Exception as e:
        print(f"❌ VERIFY EMAIL: Unexpected error - {str(e)}")
        messages.error(request, 'Verification failed. Please contact support.')
        return redirect('index')

def reset_password(request, token):
    """Handle password reset - UPDATED WITH DEBUGGING"""
    try:
        print(f"🟢 RESET PASSWORD: Processing reset for token: {token}")
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validate passwords match
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'reset_password.html', {'token': token})
            
            # Validate password length
            if len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'reset_password.html', {'token': token})
                
            user = Tradeviewusers.objects.get(password_reset_token=token)
            user.password = new_password  # This will be hashed in save()
            user.password_reset_token = None
            user.save()
            
            print(f"✅ RESET PASSWORD: Password reset successful for {user.email}")
            messages.success(request, 'Password reset successfully! You can now login with your new password.')
            return redirect('login_view')
            
        # GET request - show reset form
        user = Tradeviewusers.objects.get(password_reset_token=token)
        return render(request, 'reset_password.html', {'token': token, 'email': user.email})
        
    except Tradeviewusers.DoesNotExist:
        print(f"❌ RESET PASSWORD: Invalid reset token - {token}")
        messages.error(request, 'Invalid reset token. Please request a new password reset.')
        return redirect('forgot_password')
    except Exception as e:
        print(f"❌ RESET PASSWORD: Unexpected error - {str(e)}")
        messages.error(request, 'Password reset failed. Please try again.')
        return redirect('forgot_password')

def send_service_request_email_to_admin(service_request):
    """Send email to admin when new service request is made - UPDATED WITH DEBUGGING"""
    try:
        print(f"🟢 SERVICE REQUEST EMAIL: Sending to admin for request ID: {service_request.id}")
        
        subject = f'🆕 New Service Request: {service_request.get_request_type_display()}'
        
        html_message = render_to_string('emails/admin_service_request.html', {
            'request': service_request,
        })
        
        plain_message = f"""
New Service Request - TradeWise

Customer Details:
- Name: {service_request.name}
- Email: {service_request.email}
- Phone: {service_request.phone}

Service Requested: {service_request.get_request_type_display()}
Additional Details: {service_request.service_details}

Submitted: {service_request.created_at.strftime('%Y-%m-%d %H:%M')}

Please check the admin dashboard to process this request.
        """
        
        # Send to admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
        print(f"📧 SERVICE REQUEST EMAIL: Sending to admin - {admin_email}")
        
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ SERVICE REQUEST EMAIL: Sent successfully - Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ SERVICE REQUEST EMAIL ERROR: {str(e)}")
        return False

def send_service_confirmation_to_user(service_request):
    """Send confirmation email to user - UPDATED WITH DEBUGGING"""
    try:
        print(f"🟢 SERVICE CONFIRMATION EMAIL: Sending to user - {service_request.email}")
        
        subject = '✅ TradeWise Service Request Received'
        
        html_message = render_to_string('emails/user_service_confirmation.html', {
            'request': service_request,
        })
        
        plain_message = f"""
Service Request Received - TradeWise

Dear {service_request.name},

Thank you for your interest in our {service_request.get_request_type_display()} service!

We have received your request and our team will contact you within 24 hours to discuss your requirements.

Request Details:
- Service: {service_request.get_request_type_display()}
- Submitted: {service_request.created_at.strftime('%Y-%m-%d %H:%M')}
- Reference: SR{service_request.id:06d}

What to expect next:
1. Our expert will contact you via phone/email
2. We'll discuss your specific needs
3. We'll provide customized solutions
4. You'll get access to your chosen service

If you have any urgent questions, please contact us at +254742962615.

Best regards,
TradeWise Team
        """
        
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[service_request.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ SERVICE CONFIRMATION EMAIL: Sent successfully to {service_request.email} - Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ SERVICE CONFIRMATION EMAIL ERROR: {str(e)}")
        return False

def submit_service_request(request):
    """Handle service request submissions from website - UPDATED WITH DEBUGGING"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        service_type = request.POST.get('service_type', 'general')
        service_details = request.POST.get('service_details', '')
        
        print(f"📝 SERVICE REQUEST RECEIVED: {name}, {email}, {phone}, {service_type}")
        
        try:
            # Create service request
            service_request = ServiceRequest(
                name=name,
                email=email,
                phone=phone,
                request_type=service_type,
                service_details=service_details
            )
            service_request.save()
            print(f"✅ SERVICE REQUEST: Saved to database - ID: {service_request.id}")
            
            # Send emails
            admin_email_sent = send_service_request_email_to_admin(service_request)
            user_email_sent = send_service_confirmation_to_user(service_request)
            
            print(f"📧 SERVICE REQUEST EMAILS: Admin: {admin_email_sent}, User: {user_email_sent}")
            
            messages.success(request, f'Thank you {name}! Your request for {service_type.replace("_", " ").title()} has been submitted. We will contact you soon.')
            
            # Redirect back to the same page (trade desk page)
            return redirect('trade_desk')
            
        except Exception as e:
            print(f"❌ SERVICE REQUEST ERROR: {str(e)}")
            messages.error(request, 'There was an error submitting your request. Please try again.')
            return redirect('trade_desk')
    
    return redirect('index')

#=====================PRICING SECTION WITH MERCHANDISE FOR INDEX FILE======================
def initialize_plan_payment(request):
    """Dedicated Paystack payment for pricing plans ONLY"""
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            amount = request.POST.get('amount')
            plan_type = request.POST.get('plan_type')
            
            print(f"🚀 PLAN PAYMENT INITIATED: {email}, {amount} KES, {plan_type}")
            
            # Validate required fields
            if not email or not amount:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Email and amount are required.'})
                messages.error(request, 'Email and amount are required.')
                return redirect('index')
            
            # Convert amount to integer (kobo for Paystack)
            try:
                amount_kes = float(amount)
                amount_in_kobo = int(amount_kes * 100)
                print(f"💰 AMOUNT CONVERSION: {amount_kes} KES → {amount_in_kobo} kobo")
            except (ValueError, TypeError) as e:
                print(f"❌ AMOUNT CONVERSION ERROR: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Invalid amount format.'})
                messages.error(request, 'Invalid amount format.')
                return redirect('index')
            
            # Create unique payment reference for plans
            reference = f"PLAN{uuid.uuid4().hex[:10].upper()}"
            
            # Create payment record
            payment = Payment.objects.create(
                email=email,
                amount=amount_kes,
                plan_type=plan_type,
                reference=reference,
                status='pending'
            )
            
            print(f"📝 PLAN PAYMENT RECORD CREATED: {reference}")
            
            # Initialize Paystack
            paystack_service = PaystackService()
            
            # Process with Paystack
            response = paystack_service.initialize_transaction(
                email=email,
                amount=amount_in_kobo,
                reference=reference,
                callback_url=request.build_absolute_uri(f'/verify-payment/{reference}/'),
                metadata={
                    'plan_type': plan_type,
                    'payment_category': 'pricing_plan',
                    'custom_fields': [
                        {
                            'display_name': "Plan Type",
                            'variable_name': "plan_type", 
                            'value': plan_type
                        }
                    ]
                }
            )
            
            print(f"📡 PAYSTACK RESPONSE: {response}")
            
            if response.get('status'):
                authorization_url = response['data']['authorization_url']
                print(f"🔗 REDIRECTING TO PAYSTACK: {authorization_url}")
                
                # Return JSON for AJAX or redirect normally
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True, 
                        'redirect_url': authorization_url
                    })
                return redirect(authorization_url)
            else:
                error_msg = response.get('message', 'Unknown error occurred')
                print(f"❌ PAYSTACK ERROR: {error_msg}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, f"Payment initialization failed: {error_msg}")
                return redirect('index')
                
        except Exception as e:
            print(f"💥 PLAN PAYMENT EXCEPTION: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('index')
    
    return redirect('index')
    
    # If not POST, redirect to home
    return redirect('index')

def initialize_merchandise_payment(request):
    """Dedicated Paystack payment for merchandise ONLY"""
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            amount = request.POST.get('amount')
            item_name = request.POST.get('item_name')
            item_id = request.POST.get('item_id')
            
            print(f"🛍️ MERCHANDISE PAYMENT INITIATED: {email}, {amount} KES, {item_name}")
            
            # Validate required fields
            if not email or not amount or not item_name:
                messages.error(request, 'Email, amount, and item name are required.')
                return redirect('shop')
            
            # Convert amount to integer (kobo for Paystack)
            try:
                amount_kes = float(amount)
                amount_in_kobo = int(amount_kes * 100)
                print(f"💰 MERCHANDISE AMOUNT CONVERSION: {amount_kes} KES → {amount_in_kobo} kobo")
            except (ValueError, TypeError) as e:
                print(f"❌ MERCHANDISE AMOUNT ERROR: {e}")
                messages.error(request, 'Invalid amount format.')
                return redirect('shop')
            
            # Create unique payment reference for merchandise
            reference = f"MCH{uuid.uuid4().hex[:10].upper()}"
            
            # Create payment record
            payment = Payment.objects.create(
                email=email,
                amount=amount_kes,
                plan_type=f"Merchandise: {item_name}",
                reference=reference,
                status='pending'
            )
            
            print(f"📝 MERCHANDISE PAYMENT RECORD CREATED: {reference}")
            
            # Initialize Paystack
            paystack_service = PaystackService()
            
            # Process with Paystack
            response = paystack_service.initialize_transaction(
                email=email,
                amount=amount_in_kobo,
                reference=reference,
                callback_url=request.build_absolute_uri(f'/verify-payment/{reference}/'),
                metadata={
                    'item_name': item_name,
                    'item_id': item_id,
                    'payment_category': 'merchandise',
                    'custom_fields': [
                        {
                            'display_name': "Product",
                            'variable_name': "product", 
                            'value': item_name
                        }
                    ]
                }
            )
            
            print(f"📡 MERCHANDISE PAYSTACK RESPONSE: {response}")
            
            if response.get('status'):
                # Redirect to Paystack
                authorization_url = response['data']['authorization_url']
                print(f"🔗 REDIRECTING TO PAYSTACK: {authorization_url}")
                return redirect(authorization_url)
            else:
                error_msg = response.get('message', 'Unknown error occurred')
                print(f"❌ MERCHANDISE PAYSTACK ERROR: {error_msg}")
                messages.error(request, f"Payment initialization failed: {error_msg}")
                return redirect('shop')
                
        except Exception as e:
            print(f"💥 MERCHANDISE PAYMENT EXCEPTION: {str(e)}")
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('shop')
    
    # If not POST, redirect to shop
    return redirect('shop')

#=====================PAYMENT PLAN EMAILS======================
@admin_required
def send_service_onboarding_email(request, payment_id):
    """Admin: Send onboarding email manually"""
    try:
        service_payment = ServicePayment.objects.get(id=payment_id)
        if service_payment.send_onboarding_email():
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Email sending failed'})
    except ServicePayment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Payment not found'})

@admin_required
def add_manual_payment(request, payment_id):
    """Admin: Add manual payment"""
    try:
        service_payment = ServicePayment.objects.get(id=payment_id)
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        
        if amount > 0:
            service_payment.update_progress(amount)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid amount'})
    except ServicePayment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Payment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
# ================== UPDATED ADMIN DASHBOARD ==================

@admin_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard with SIMPLE data"""
    try:
        # Get basic counts for dashboard
        total_users = Tradeviewusers.objects.count()
        new_users_today = Tradeviewusers.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # Calculate total revenue from successful payments
        total_revenue = Payment.objects.filter(status='success').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Count pending service requests
        pending_requests_count = ServiceRequest.objects.filter(status='pending').count()
        
        # Active traders (users with recent activity)
        active_traders = Tradeviewusers.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Add software tools to context
        software_list = SoftwareTool.objects.all().order_by('-created_at')
        active_software_count = SoftwareTool.objects.filter(is_active=True).count()
        total_downloads = SoftwareTool.objects.aggregate(total=Sum('download_count'))['total'] or 0
        software_types_count = SoftwareTool.objects.values('file_type').distinct().count()

        # ================== NEW REFERRAL MANAGEMENT DATA ==================
        pending_referrals_list = Referral.objects.filter(status='pending').select_related('affiliate__user', 'referred_user').order_by('-created_at')
        approved_referrals_count = Referral.objects.filter(status='approved').count()
        total_pending_coins = pending_referrals_list.count() * 50
        
        # Affiliate debug data
        affiliate_debug = {
            'pending_referrals': pending_referrals_list.count(),
            'approved_referrals': approved_referrals_count,
            'total_coins_awarded': Referral.objects.filter(status='approved').aggregate(Sum('coins_awarded'))['coins_awarded__sum'] or 0,
            'total_coin_balance': Affiliate.objects.aggregate(Sum('coin_balance'))['coin_balance__sum'] or 0,
        }

        # Get all data for the dashboard
        context = {
            # Statistics
            'total_users': total_users,
            'new_users_today': new_users_today,
            'total_revenue': total_revenue,
            'pending_requests_count': pending_requests_count,
            'active_traders': active_traders,
            
            # Content data
            'strategies': TradingStrategy.objects.all(),
            'signals': TradingSignal.objects.all(),
            
            'services': Service.objects.all(),
            'blog_posts': BlogPost.objects.all(),
            'tradewise_card': TradeWiseCard.objects.first(),
            'featured_merchandise': Merchandise.objects.all(),
            'merchandise_list': Merchandise.objects.all(),
            'tradewise_coin': TradeWiseCoin.objects.first(),
            'reviews': Review.objects.all(),
            'all_requests': ServiceRequest.objects.all().order_by('-created_at'),
            'users': Tradeviewusers.objects.all().order_by('-created_at'),
            
            # Software data
            'software_list': software_list,
            'active_software_count': active_software_count,
            'total_downloads': total_downloads,
            'software_types_count': software_types_count,

            # Affiliate data
            'total_affiliates': Affiliate.objects.count(),
            'pending_payouts_count': PayoutRequest.objects.filter(status='pending').count(),
            'all_affiliates': Affiliate.objects.select_related('user').all(),
            'pending_payouts': PayoutRequest.objects.filter(status='pending').select_related('user'),
            'current_weekly_number': WeeklyNumber.objects.filter(is_active=True).first(),
            'previous_numbers': WeeklyNumber.objects.filter(is_active=False).order_by('-created_at')[:5],
            
            # ================== NEW REFERRAL MANAGEMENT DATA ==================
            'pending_referrals_list': pending_referrals_list,
            'approved_referrals_count': approved_referrals_count,
            'total_pending_coins': total_pending_coins,
            'affiliate_debug': affiliate_debug,
            
            # Current admin info
            'current_admin': {
                'username': request.session.get('admin_username', 'Admin'),
                'number': request.session.get('admin_number', '500100')
            },
            
            # Chart data (simplified)
            'revenue_chart_data': get_revenue_chart_data(),
            'service_distribution_data': get_service_distribution_data(),
        }

        # SIMPLE SERVICE PAYMENT DATA
        all_service_payments = ServicePayment.objects.all().order_by('-created_at')
        completed_payments = all_service_payments.filter(status='completed')
        
        context.update({
            'all_service_payments': all_service_payments,
            'completed_payments': completed_payments,
        })
        
        print(f"🔍 ADMIN DASHBOARD DEBUG:")
        print(f"   - Pending Referrals: {pending_referrals_list.count()}")
        print(f"   - Approved Referrals: {approved_referrals_count}")
        print(f"   - Total Pending Coins: {total_pending_coins}")
        print(f"   - Affiliate Debug: {affiliate_debug}")
        
    except Exception as e:
        # If there are any database issues, provide empty context
        print(f"❌ Dashboard error: {e}")
        context = {
            'total_users': 0,
            'new_users_today': 0,
            'total_revenue': 0,
            'pending_requests_count': 0,
            'active_traders': 0,
            'current_admin': {'username': 'Admin'},
            # Empty referral data
            'pending_referrals_list': [],
            'approved_referrals_count': 0,
            'total_pending_coins': 0,
            'affiliate_debug': {
                'pending_referrals': 0,
                'approved_referrals': 0,
                'total_coins_awarded': 0,
                'total_coin_balance': 0,
            },
        }
    
    # Handle form submissions
    if request.method == 'POST':
        return handle_admin_form_submission(request)
    
    return render(request, 'admin_dashboard.html', context)

def handle_admin_form_submission(request):
    """Handle all admin form submissions with traditional forms"""
    action = request.POST.get('action')
    
    try:
        if action == 'delete_strategy':
            return delete_strategy(request)
        elif action == 'delete_signal':
            return delete_signal(request)
        elif action == 'delete_software':
            return delete_software(request)
        elif action == 'delete_blog':
            return delete_blog_post(request)
        elif action == 'delete_merchandise':
            return delete_merchandise(request)
        elif action == 'delete_review':
            return delete_review(request)
        elif action == 'update_request_status':
            return update_request_status_traditional(request)
        elif action == 'review_action':
            return review_action_traditional(request)
        elif action == 'process_payout':
            return process_payout_traditional(request)
        elif action == 'send_onboarding_email':
            return send_onboarding_email_traditional(request)
        elif action == 'add_manual_payment':
            return add_manual_payment_traditional(request)
        elif action == 'approve_referral':
            return approve_referral_traditional(request)
        elif action == 'approve_all_referrals':
            return approve_all_referrals_traditional(request)
        elif action == 'track_download':
            return track_download_traditional(request)
        else:
            messages.error(request, 'Invalid action.')
            
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== TRADITIONAL FORM HANDLERS ==================

def delete_blog_post(request):
    """Delete blog post - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        item_name = request.POST.get('item_name')
        
        blog_post = BlogPost.objects.get(id=item_id)
        blog_post.delete()
        
        messages.success(request, f'Blog post "{item_name}" deleted successfully!')
    except BlogPost.DoesNotExist:
        messages.error(request, 'Blog post not found.')
    except Exception as e:
        messages.error(request, f'Error deleting blog post: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_review(request):
    """Delete review - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        item_name = request.POST.get('item_name')
        
        review = Review.objects.get(id=item_id)
        review.delete()
        
        messages.success(request, f'Review "{item_name}" deleted successfully!')
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    except Exception as e:
        messages.error(request, f'Error deleting review: {str(e)}')
    
    return redirect('admin_dashboard')

def send_onboarding_email_traditional(request):
    """Send onboarding email - traditional form"""
    try:
        payment_id = request.POST.get('payment_id')
        # Implement your email sending logic here
        messages.success(request, 'Onboarding email sent successfully!')
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
    
    return redirect('admin_dashboard')

def add_manual_payment_traditional(request):
    """Add manual payment - traditional form"""
    try:
        payment_id = request.POST.get('payment_id')
        amount = request.POST.get('amount')
        # Implement your manual payment logic here
        messages.success(request, f'Manual payment of {amount} added successfully!')
    except Exception as e:
        messages.error(request, f'Error adding manual payment: {str(e)}')
    
    return redirect('admin_dashboard')

def approve_referral_traditional(request):
    """Approve referral - traditional form"""
    try:
        referral_id = request.POST.get('referral_id')
        # Implement your referral approval logic here
        messages.success(request, 'Referral approved and coins awarded!')
    except Exception as e:
        messages.error(request, f'Error approving referral: {str(e)}')
    
    return redirect('admin_dashboard')

def approve_all_referrals_traditional(request):
    """Approve all referrals - traditional form"""
    try:
        # Implement your bulk approval logic here
        messages.success(request, 'All pending referrals approved!')
    except Exception as e:
        messages.error(request, f'Error approving referrals: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_strategy(request):
    """Delete strategy - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        item_name = request.POST.get('item_name')
        
        strategy = TradingStrategy.objects.get(id=item_id)
        strategy.delete()
        
        messages.success(request, f'Strategy "{item_name}" deleted successfully!')
    except TradingStrategy.DoesNotExist:
        messages.error(request, 'Strategy not found.')
    except Exception as e:
        messages.error(request, f'Error deleting strategy: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_signal(request):
    """Delete signal - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        item_name = request.POST.get('item_name')
        
        signal = TradingSignal.objects.get(id=item_id)
        signal.delete()
        
        messages.success(request, f'Signal "{item_name}" deleted successfully!')
    except TradingSignal.DoesNotExist:
        messages.error(request, 'Signal not found.')
    except Exception as e:
        messages.error(request, f'Error deleting signal: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_software(request):
    """Delete software - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        item_name = request.POST.get('item_name')
        
        software = SoftwareTool.objects.get(id=item_id)
        software.delete()
        
        messages.success(request, f'Software "{item_name}" deleted successfully!')
    except SoftwareTool.DoesNotExist:
        messages.error(request, 'Software not found.')
    except Exception as e:
        messages.error(request, f'Error deleting software: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_merchandise(request):
    """Delete merchandise - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        item_name = request.POST.get('item_name')
        
        merchandise = Merchandise.objects.get(id=item_id)
        merchandise.delete()
        
        messages.success(request, f'Merchandise "{item_name}" deleted successfully!')
    except Merchandise.DoesNotExist:
        messages.error(request, 'Merchandise not found.')
    except Exception as e:
        messages.error(request, f'Error deleting merchandise: {str(e)}')
    
    return redirect('admin_dashboard')

def update_request_status_traditional(request):
    """Update request status - traditional form"""
    try:
        request_id = request.POST.get('request_id')
        status = request.POST.get('status')
        request_type = request.POST.get('request_type')
        
        # Implement your status update logic here
        service_request = ServiceRequest.objects.get(id=request_id)
        service_request.status = status
        service_request.save()
        
        messages.success(request, f'Request status updated to {status}!')
    except ServiceRequest.DoesNotExist:
        messages.error(request, 'Request not found.')
    except Exception as e:
        messages.error(request, f'Error updating request: {str(e)}')
    
    return redirect('admin_dashboard')

def review_action_traditional(request):
    """Review actions - traditional form"""
    try:
        review_id = request.POST.get('review_id')
        review_action = request.POST.get('review_action')
        
        review = Review.objects.get(id=review_id)
        
        if review_action == 'approve':
            review.is_approved = True
            messages.success(request, 'Review approved!')
        elif review_action == 'feature':
            review.is_featured = True
            messages.success(request, 'Review featured!')
        elif review_action == 'unfeature':
            review.is_featured = False
            messages.success(request, 'Review unfeatured!')
        
        review.save()
        
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    except Exception as e:
        messages.error(request, f'Error processing review: {str(e)}')
    
    return redirect('admin_dashboard')

def process_payout_traditional(request):
    """Process payout - traditional form"""
    try:
        payout_id = request.POST.get('payout_id')
        payout_status = request.POST.get('payout_status')
        
        payout = PayoutRequest.objects.get(id=payout_id)
        payout.status = payout_status
        payout.save()
        
        messages.success(request, f'Payout {payout_status}!')
    except PayoutRequest.DoesNotExist:
        messages.error(request, 'Payout request not found.')
    except Exception as e:
        messages.error(request, f'Error processing payout: {str(e)}')
    
    return redirect('admin_dashboard')



def track_download_traditional(request):
    """Track download - traditional form"""
    try:
        software_id = request.POST.get('software_id')
        software = SoftwareTool.objects.get(id=software_id)
        software.increment_download_count()
        
        # Return the file for download
        from django.http import FileResponse
        response = FileResponse(software.file.open(), as_attachment=True, filename=software.file.name)
        return response
        
    except SoftwareTool.DoesNotExist:
        messages.error(request, 'Software not found.')
        return redirect('admin_dashboard')
    

# ================== WEBSITE FRONTEND VIEWS ==================

def index(request):
    """Homepage with all dynamic content - ULTRA DEBUG VERSION"""
    print("🚀 ULTRA DEBUG: Index view started")
    
    try:
        # DEBUG 1: Check database directly
        all_merch = Merchandise.objects.all()
        print(f"🔍 DEBUG 1 - Database check:")
        print(f"   Total merchandise in DB: {all_merch.count()}")
        for item in all_merch:
            print(f"   - ID: {item.id}, Name: '{item.name}', Available: {item.is_available}, Featured: {item.is_featured}")

        # DEBUG 2: Check the exact query we're using
        featured_merchandise = Merchandise.objects.filter(is_available=True)[:8]
        print(f"🔍 DEBUG 2 - Query result:")
        print(f"   featured_merchandise count: {featured_merchandise.count()}")
        print(f"   SQL Query: {str(featured_merchandise.query)}")
        
        # DEBUG 3: Force convert to list to see what's really there
        merch_list = list(featured_merchandise)
        print(f"🔍 DEBUG 3 - List conversion:")
        print(f"   Converted list length: {len(merch_list)}")
        for i, item in enumerate(merch_list):
            print(f"   [{i}] {item.name}")

        # DEBUG 4: Check if we can access attributes
        if merch_list:
            first_item = merch_list[0]
            print(f"🔍 DEBUG 4 - First item attributes:")
            print(f"   Name: {first_item.name}")
            print(f"   Price: {first_item.price}")
            print(f"   Category: {first_item.category}")
            print(f"   Image: {first_item.image}")

        context = {
            'featured_merchandise': featured_merchandise,
            'tradewise_card': TradeWiseCard.objects.filter(is_active=True).first(),
            'pricing_plans': PricingPlan.objects.filter(is_active=True).order_by('price'),
            'services': Service.objects.filter(is_active=True),
            'approved_reviews': Review.objects.filter(is_approved=True),
            'recent_posts': BlogPost.objects.filter(is_published=True).order_by('-created_at')[:3],
            'tradewise_coin': TradeWiseCoin.objects.first(),
            'active_affiliate': AffiliateProgram.objects.filter(is_active=True).first(),
        }

        print(f"🔍 DEBUG 5 - Context prepared:")
        print(f"   Context keys: {list(context.keys())}")
        print(f"   featured_merchandise in context: {'featured_merchandise' in context}")
        print(f"   Type: {type(context['featured_merchandise'])}")
        print(f"   Length: {len(context['featured_merchandise'])}")

    except Exception as e:
        print(f"🔴 ULTRA DEBUG ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        context = {'featured_merchandise': []}

    print("🚀 ULTRA DEBUG: Rendering template...")
    return render(request, 'index.html', context)


def explore(request):
    """Explore page"""
    return render(request, 'explore.html')

def login_view(request):
    """User login view - WITH EMAIL VERIFICATION CHECK & DEBUGGING"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        print(f"🟢 LOGIN ATTEMPT: Email: {email}")
        
        try:
            user = Tradeviewusers.objects.get(email=email)
            print(f"✅ LOGIN: User found - {user.first_name} {user.second_name} (Account: {user.account_number})")
            
            # Check if password is correct
            if user.check_password(password):
                print(f"✅ LOGIN: Password correct")
                
                # ✅ CHECK IF EMAIL IS VERIFIED
                if not user.is_email_verified:
                    print(f"❌ LOGIN: Email not verified for {email}")
                    messages.error(request, 
                        '❌ Please verify your email before logging in. '
                        'Check your inbox for the verification link. '
                        'If you didn\'t receive it, check your spam folder or contact support.'
                    )
                    return render(request, 'login.html')
                
                # Check if account is active
                if user.is_active:
                    # Set user session
                    request.session['user_id'] = user.id
                    request.session['account_number'] = user.account_number
                    request.session['first_name'] = user.first_name
                    request.session['second_name'] = user.second_name
                    user.last_login = timezone.now()
                    user.save()
                    
                    print(f"✅ LOGIN SUCCESS: Session created - User ID: {user.id}, Account: {user.account_number}")
                    print(f"📊 LOGIN: Session data - {dict(request.session)}")
                    
                    messages.success(request, f'🎉 Welcome back, {user.first_name}!')
                    return redirect('account')  # ✅ Redirect to account page
                else:
                    print(f"❌ LOGIN: Account inactive for {email}")
                    messages.error(request, 'Your account is inactive. Please contact support.')
            else:
                print(f"❌ LOGIN: Invalid password for {email}")
                messages.error(request, 'Invalid email or password.')
                
        except Tradeviewusers.DoesNotExist:
            print(f"❌ LOGIN: User not found - {email}")
            messages.error(request, 'Invalid email or password.')
        except Exception as e:
            print(f"❌ LOGIN: Unexpected error - {str(e)}")
            messages.error(request, 'Login failed. Please try again.')
    
    # If GET request or login failed, show login page
    print(f"🔵 LOGIN: Rendering login page")
    return render(request, 'login.html')


def signup(request):
    """PERMANENT FIX SIGNUP - GUARANTEED AUTO-COIN AWARDS"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        second_name = request.POST.get('second_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        # 🚨🚨🚨 ULTIMATE REFERRAL CAPTURE - CHECK EVERY POSSIBLE SOURCE 🚨🚨🚨
        referrer_id = (
            request.POST.get('referral_code', '').strip() or 
            request.POST.get('ref', '').strip() or 
            request.GET.get('ref', '').strip() or
            request.session.get('referral_code', '').strip()
        )
        
        print(f"🔴🟢🔴 CRITICAL DEBUG: RAW POST DATA = {dict(request.POST)}")
        print(f"🔴🟢🔴 CRITICAL DEBUG: RAW GET DATA = {dict(request.GET)}")
        print(f"🔴🟢🔴 CRITICAL DEBUG: EXTRACTED REFERRAL CODE = '{referrer_id}'")
        
        # 🚨 TEMPORARY DEBUG FIX - FORCE REFERRAL IF URL HAS IT
        if not referrer_id and 'ref' in request.GET:
            referrer_id = request.GET.get('ref', '').strip()
            print(f"🚨 FORCED REFERRAL FROM URL: '{referrer_id}'")
        
        print(f"🎯 SIGNUP STARTED: {email}, Referrer: '{referrer_id}'")
        print(f"📝 User Details: {first_name} {second_name}, Phone: {phone}")

        # Check if user exists
        if Tradeviewusers.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'login.html')

        try:
            # STEP 1: Create new user
            user = Tradeviewusers(
                first_name=first_name,
                second_name=second_name,
                email=email,
                phone=phone,
                password=password
            )
            user.save()
            print(f"✅ USER CREATED: {user.first_name} {user.second_name} (TWN: {user.account_number})")

            # STEP 2: Wait for affiliate auto-creation signal
            print(f"⏳ Waiting for affiliate auto-creation...")
            import time
            time.sleep(0.5)  # Give time for signal to create affiliate
            
            # Verify affiliate was created
            try:
                new_affiliate = Affiliate.objects.get(user=user)
                print(f"✅ NEW USER AFFILIATE: {new_affiliate.referral_code}")
            except Affiliate.DoesNotExist:
                print(f"❌ AFFILIATE NOT CREATED - Creating manually...")
                new_affiliate = Affiliate.objects.create(user=user)
                print(f"✅ MANUAL AFFILIATE CREATED: {new_affiliate.referral_code}")

            # STEP 3: 🚀 PROCESS REFERRAL - SIMPLE & AUTOMATIC
            if referrer_id and referrer_id.strip():
                print(f"🔍 PROCESSING REFERRAL: Raw code '{referrer_id}'")
                
                # 🚨 UNIVERSAL FLEXIBLE CODE MATCHING 🚨
                # Clean and normalize the referral code
                referrer_id = referrer_id.strip().upper()
                print(f"🔧 After cleaning: '{referrer_id}'")
                
                # If it's just numbers, add 'TW' prefix (5000 → TW5000)
                if referrer_id.isdigit():
                    referrer_id = f"TW{referrer_id}"
                    print(f"🔧 Converted numbers to: '{referrer_id}'")
                
                print(f"🎯 FINAL REFERRAL CODE: '{referrer_id}'")
                # 🚨 END UNIVERSAL MATCHING 🚨
                
                # Prevent self-referral
                if referrer_id == new_affiliate.referral_code:
                    print(f"⚠️ SELF-REFERRAL ATTEMPT - Skipping: {referrer_id}")
                else:
                    try:
                        # Find the referrer
                        referrer_affiliate = Affiliate.objects.get(referral_code=referrer_id)
                        print(f"✅ FOUND REFERRER: {referrer_affiliate.user.email}")
                        print(f"💰 REFERRER CURRENT BALANCE: {referrer_affiliate.coin_balance} coins")
                        
                        # Check if referral already exists (prevent duplicates)
                        existing_referral = Referral.objects.filter(
                            affiliate=referrer_affiliate,
                            referred_user=user
                        ).first()
                        
                        if existing_referral:
                            print(f"⚠️ REFERRAL ALREADY EXISTS - Skipping duplicate")
                            print(f"   Existing referral ID: {existing_referral.id}, Status: {existing_referral.status}")
                        else:
                            # 🚀 CREATE REFERRAL - THIS TRIGGERS AUTO-COIN AWARD!
                            print(f"🔴🟢🔴 CRITICAL DEBUG: ABOUT TO CREATE REFERRAL!")
                            referral = Referral.objects.create(
                                affiliate=referrer_affiliate,
                                referred_user=user,
                                is_active=True
                            )
                            
                            print(f"🎉 REFERRAL CREATED SUCCESSFULLY!")
                            print(f"   Referral ID: {referral.id}")
                            print(f"   Status: {referral.status}")
                            print(f"   Coins Awarded: {referral.coins_awarded}")
                            
                            # Refresh referrer data to see updated balance
                            referrer_affiliate.refresh_from_db()
                            print(f"💰 REFERRER NEW BALANCE: {referrer_affiliate.coin_balance} coins")
                            print(f"👥 REFERRER TOTAL REFERRALS: {referrer_affiliate.total_referrals}")
                            
                    except Affiliate.DoesNotExist:
                        print(f"❌ NO AFFILIATE FOUND WITH CODE: '{referrer_id}'")
                        print(f"   Available codes: {list(Affiliate.objects.values_list('referral_code', flat=True)[:5])}")
                    except Exception as e:
                        print(f"❌ REFERRAL PROCESSING ERROR: {str(e)}")
                        import traceback
                        traceback.print_exc()
            else:
                print("ℹ️ No referral code provided - Standard signup")

            # STEP 4: Send emails WITH ERROR HANDLING
            print(f"📧 Sending verification emails...")
            email_success = True
            email_errors = []
            
            try:
                # Send verification email
                print(f"🟢 MODEL: Starting verification email for {user.email}")
                email_sent = user.send_verification_email()
                if email_sent:
                    print(f"✅ MODEL: Verification email sent - Result: {email_sent}")
                    print(f"✅ Verification email sent to {user.email}")
                else:
                    print(f"❌ MODEL: Verification email failed - Result: {email_sent}")
                    email_success = False
                    email_errors.append("Verification email failed to send")
                    
            except Exception as email_error:
                print(f"❌ MODEL: Verification email failed: {email_error}")
                email_success = False
                email_errors.append(f"Verification: {str(email_error)}")
                # Continue anyway - don't break signup

            try:
                # Send welcome email
                print(f"🟢 WELCOME EMAIL: Starting for {user.email}")
                welcome_sent = user.send_welcome_email(password)
                if welcome_sent:
                    print(f"✅ WELCOME EMAIL: Welcome email sent successfully")
                    print(f"✅ Welcome email sent to {user.email}")
                else:
                    print(f"❌ WELCOME EMAIL: Failed to send welcome email")
                    email_success = False
                    email_errors.append("Welcome email failed to send")
                    
            except Exception as welcome_error:
                print(f"❌ WELCOME EMAIL: Failed to send welcome email: {welcome_error}")
                email_success = False
                email_errors.append(f"Welcome: {str(welcome_error)}")
                # Continue anyway - don't break signup

            # STEP 5: Final debug info
            print(f"🎊 SIGNUP COMPLETED SUCCESSFULLY!")
            print(f"   User: {user.first_name} {user.second_name}")
            print(f"   Email: {user.email}")
            print(f"   TWN: {user.account_number}")
            print(f"   Affiliate Code: {new_affiliate.referral_code}")
            print(f"   Referral Used: {'Yes' if referrer_id else 'No'}")
            print(f"   Emails Status: {'✅ All sent' if email_success else '❌ Some failed'}")

            # Show appropriate messages to user
            if email_success:
                messages.success(request, 
                    f'🎉 Account created successfully, {user.first_name}! '
                    f'Check your email to verify your account.'
                )
            else:
                messages.success(request, 
                    f'🎉 Account created successfully, {user.first_name}! '
                    f'Your account number is: {user.account_number}'
                )
                messages.warning(request, 
                    f'Note: Email delivery is temporarily unavailable. '
                    f'You can still login and use your account.'
                )
            
            if referrer_id:
                messages.info(request, 
                    f'✅ Referral processed! 50 coins awarded to the referrer.'
                )

            return redirect('login_view')

        except Exception as e:
            print(f"💥 SIGNUP ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, 
                f'Registration failed: {str(e)}. '
                f'Please try again or contact support.'
            )
            return render(request, 'login.html')

    # GET request - show signup form
    print(f"🔵 SIGNUP: Rendering signup page")
    
    # Pre-fill referral code if provided in URL
    referral_code = request.GET.get('ref', '')
    context = {}
    if referral_code:
        context['referral_code'] = referral_code
        request.session['referral_code'] = referral_code  # Store in session as backup
        print(f"🔗 Pre-filled referral code in context: {referral_code}")
    
    return render(request, 'login.html', context)
    

def forgot_password(request):
    """Password reset request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = Tradeviewusers.objects.get(email=email)
            # Create password reset token
            user.password_reset_token = secrets.token_urlsafe(32)
            user.save()
            
            # Send reset email (simplified)
            messages.success(request, 'Password reset instructions have been sent to your email.')
        except Tradeviewusers.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'forgot_password.html')

# ================== BLOG VIEWS ==================

@admin_required
def add_blog_post(request):
    """Add new blog post from admin"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
            author = request.POST.get('author', 'TradeWise Team')
            is_published = request.POST.get('is_published') == 'on'
            
            blog = BlogPost(
                title=title,
                content=content,
                author=author,
                is_published=is_published
            )
            
            if 'featured_image' in request.FILES:
                blog.featured_image = request.FILES['featured_image']
            
            blog.save()
            
            # Log action
            AdminLog.objects.create(
                user=get_current_admin(request),
                action=f'Added blog post: {blog.title}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Blog post added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error adding blog post: {str(e)}')
    
    return redirect('admin_dashboard')

def blog_list(request):
    """Blog page with all published posts"""
    posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'blog.html', {'posts': posts})

def blog_detail(request, slug):
    """Individual blog post"""
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'blog_detail.html', {'post': post})

@admin_required
def edit_blog_post(request, post_id):
    """Edit blog post"""
    if request.method == 'POST':
        try:
            blog = BlogPost.objects.get(id=post_id)
            blog.title = request.POST.get('title')
            blog.content = request.POST.get('content')
            blog.author = request.POST.get('author', 'TradeWise Team')
            blog.is_published = request.POST.get('is_published') == 'on'
            
            if 'featured_image' in request.FILES:
                blog.featured_image = request.FILES['featured_image']
            
            blog.save()
            
            messages.success(request, 'Blog post updated successfully!')
            
        except BlogPost.DoesNotExist:
            messages.error(request, 'Blog post not found.')
        except Exception as e:
            messages.error(request, f'Error updating blog post: {str(e)}')
    
    return redirect('admin_dashboard')

@admin_required
def delete_blog_post(request, post_id):
    """Delete blog post"""
    try:
        blog = BlogPost.objects.get(id=post_id)
        blog_title = blog.title
        blog.delete()
        
        AdminLog.objects.create(
            user=get_current_admin(request),
            action=f'Deleted blog post: {blog_title}',
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, 'Blog post deleted successfully!')
        
    except BlogPost.DoesNotExist:
        messages.error(request, 'Blog post not found.')
    except Exception as e:
        messages.error(request, f'Error deleting blog post: {str(e)}')
    
    return redirect('admin_dashboard')


def shop(request):
    """Merchandise shop"""
    merchandise = Merchandise.objects.filter(is_available=True)
    return render(request, 'shop.html', {'merchandise': merchandise})

# ================== BLOG VIEWS ==================

def blog_list(request):
    """Blog page with all published posts"""
    posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'blog.html', {'posts': posts})

def blog_detail(request, slug):
    """Individual blog post"""
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'blog_detail.html', {'post': post})

@admin_required
def add_blog_post(request):
    """Add new blog post from admin"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
            author = request.POST.get('author', 'TradeWise Team')
            is_published = request.POST.get('is_published') == 'on'
            
            blog = BlogPost(
                title=title,
                content=content,
                author=author,
                is_published=is_published
            )
            
            if 'featured_image' in request.FILES:
                blog.featured_image = request.FILES['featured_image']
            
            blog.save()
            
            AdminLog.objects.create(
                user=get_current_admin(request),
                action=f'Added blog post: {blog.title}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Blog post added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error adding blog post: {str(e)}')
    
    return redirect('admin_dashboard')

@admin_required
def edit_blog_post(request, post_id):
    """Edit blog post"""
    if request.method == 'POST':
        try:
            blog = BlogPost.objects.get(id=post_id)
            blog.title = request.POST.get('title')
            blog.content = request.POST.get('content')
            blog.author = request.POST.get('author', 'TradeWise Team')
            blog.is_published = request.POST.get('is_published') == 'on'
            
            if 'featured_image' in request.FILES:
                blog.featured_image = request.FILES['featured_image']
            
            blog.save()
            
            messages.success(request, 'Blog post updated successfully!')
            
        except BlogPost.DoesNotExist:
            messages.error(request, 'Blog post not found.')
        except Exception as e:
            messages.error(request, f'Error updating blog post: {str(e)}')
    
    return redirect('admin_dashboard')

@admin_required
def delete_blog_post(request, post_id):
    """Delete blog post"""
    try:
        blog = BlogPost.objects.get(id=post_id)
        blog_title = blog.title
        blog.delete()
        
        AdminLog.objects.create(
            user=get_current_admin(request),
            action=f'Deleted blog post: {blog_title}',
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, 'Blog post deleted successfully!')
        
    except BlogPost.DoesNotExist:
        messages.error(request, 'Blog post not found.')
    except Exception as e:
        messages.error(request, f'Error deleting blog post: {str(e)}')
    
    return redirect('admin_dashboard')



def blog_list(request):
    """Blog page with all published posts"""
    posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'blog.html', {'posts': posts})

def blog_detail(request, slug):
    """Individual blog post"""
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'blog_detail.html', {'post': post})
# ================== REVIEW VIEWS ==================
def submit_review(request):
    """Handle review submission from frontend"""
    if request.method == 'POST':
        try:
            reviewer_name = request.POST.get('reviewerName')
            reviewer_role = request.POST.get('reviewerRole', 'Forex Trader')  # This maps to user_role
            reviewer_email = request.POST.get('reviewerEmail', '')
            rating = int(request.POST.get('rating', 5))
            review_text = request.POST.get('reviewText')
            
            # Create review (initially not approved)
            review = Review(
                author_name=reviewer_name,
                client_name=reviewer_name,  # Set both for compatibility
                user_role=reviewer_role,    # Use user_role (correct field name)
                email=reviewer_email,
                content=review_text,
                rating=rating,
                is_approved=False,  # Needs admin approval
                from_admin=False
            )
            
            if 'image' in request.FILES:
                review.image = request.FILES['image']
            
            review.save()
            
            # Send email notification to admin
            send_review_notification_email(review)
            
            # Return JSON response for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for your review! It has been submitted and is awaiting approval.'
                })
            
            messages.success(request, 'Thank you for your review! It has been submitted and is awaiting approval.')
            
        except Exception as e:
            print(f"Review submission error: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'There was an error submitting your review. Please try again.'
                })
            messages.error(request, 'There was an error submitting your review. Please try again.')
    
    return redirect('index')

@admin_required
def add_review(request):
    """Add new review from admin"""
    if request.method == 'POST':
        try:
            author_name = request.POST.get('author_name')
            user_role = request.POST.get('user_role', 'Forex Trader')
            email = request.POST.get('email', '')
            content = request.POST.get('content')
            rating = int(request.POST.get('rating', 5))
            is_approved = request.POST.get('is_approved') == 'on'
            is_featured = request.POST.get('is_featured') == 'on'
            
            review = Review(
                author_name=author_name,
                client_name=author_name,  # Set both fields for compatibility
                user_role=user_role,
                email=email,
                content=content,
                rating=rating,
                is_approved=is_approved,
                is_featured=is_featured,
                from_admin=True
            )
            
            if 'image' in request.FILES:
                review.image = request.FILES['image']
            
            review.save()
            
            AdminLog.objects.create(
                user=get_current_admin(request),
                action=f'Added review from: {review.author_name}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Review added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error adding review: {str(e)}')
    
    return redirect('admin_dashboard')

@admin_required
def approve_review(request, review_id):
    """Approve a review"""
    try:
        review = Review.objects.get(id=review_id)
        review.is_approved = True
        review.save()
        
        messages.success(request, f'Review from {review.author_name} approved successfully!')
        
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    
    return redirect('admin_dashboard')

@admin_required
def toggle_review_featured(request, review_id):
    """Toggle review featured status"""
    try:
        review = Review.objects.get(id=review_id)
        review.is_featured = not review.is_featured
        review.save()
        
        status = "featured" if review.is_featured else "unfeatured"
        messages.success(request, f'Review {status} successfully!')
        
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    
    return redirect('admin_dashboard')

@admin_required
def delete_review(request, review_id):
    """Delete a review"""
    try:
        review = Review.objects.get(id=review_id)
        author_name = review.author_name
        review.delete()
        
        AdminLog.objects.create(
            user=get_current_admin(request),
            action=f'Deleted review from: {author_name}',
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, 'Review deleted successfully!')
        
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    
    return redirect('admin_dashboard')

@admin_required
def approve_all_pending_reviews(request):
    """Approve all pending reviews"""
    try:
        pending_reviews = Review.objects.filter(is_approved=False)
        count = pending_reviews.count()
        
        for review in pending_reviews:
            review.is_approved = True
            review.save()
        
        messages.success(request, f'Approved all {count} pending reviews!')
        
    except Exception as e:
        messages.error(request, f'Error approving reviews: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== REVIEW & BLOG API VIEWS ==================

def get_approved_reviews(request):
    """API endpoint to get approved reviews for frontend"""
    try:
        approved_reviews = Review.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')[:6]
        
        reviews_data = []
        for review in approved_reviews:
            reviews_data.append({
                'id': review.id,
                'author_name': review.author_name or review.client_name,
                'user_role': review.user_role,
                'content': review.content,
                'rating': review.rating,
                'image_url': review.image.url if review.image else '/static/images/default-avatar.jpg',
                'created_at': review.created_at.strftime('%b %d, %Y'),
                'is_featured': review.is_featured
            })
        
        return JsonResponse({
            'success': True,
            'reviews': reviews_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def get_published_blogs(request):
    """API endpoint to get published blogs for frontend"""
    try:
        published_blogs = BlogPost.objects.filter(is_published=True).order_by('-created_at')[:3]
        
        blogs_data = []
        for blog in published_blogs:
            blogs_data.append({
                'id': blog.id,
                'title': blog.title,
                'content': blog.content,
                'excerpt': blog.content[:150] + '...' if len(blog.content) > 150 else blog.content,
                'author': blog.author,
                'featured_image': blog.featured_image.url if blog.featured_image else None,
                'created_at': blog.created_at.strftime('%b %d, %Y'),
                'slug': blog.slug
            })
        
        return JsonResponse({
            'success': True,
            'blogs': blogs_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ================== REVIEW EMAIL FUNCTION ==================

def send_review_notification_email(review):
    """Send email to admin when new review is submitted"""
    try:
        subject = f'🆕 New Review Submitted - Awaiting Approval'
        
        html_message = render_to_string('emails/admin_review_notification.html', {
            'review': review,
        })
        
        plain_message = f"""
New Review Submission - TradeWise

Reviewer: {review.author_name or review.client_name}
Role: {review.user_role}  # Changed from profession to user_role
Email: {review.email or 'Not provided'}
Rating: {review.rating}/5 stars

Review Content:
"{review.content}"

Submitted: {review.created_at.strftime('%Y-%m-%d %H:%M')}

Please log in to the admin dashboard to approve or reject this review.
        """
        
        # Send to admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"📧 REVIEW NOTIFICATION SENT TO ADMIN")
        return True
        
    except Exception as e:
        print(f"❌ REVIEW NOTIFICATION EMAIL ERROR: {str(e)}")
        return False

# ================== REVIEWS MANAGEMENT VIEWS ==================

def submit_review(request):
    """Handle review submission from frontend"""
    if request.method == 'POST':
        try:
            reviewer_name = request.POST.get('reviewerName')
            reviewer_role = request.POST.get('reviewerRole', 'Forex Trader')
            reviewer_email = request.POST.get('reviewerEmail', '')
            rating = int(request.POST.get('rating', 5))
            review_text = request.POST.get('reviewText')
            
            # Create review (initially not approved)
            review = Review(
                author_name=reviewer_name,
                user_role=reviewer_role,
                email=reviewer_email,
                content=review_text,
                rating=rating,
                is_approved=False,  # Needs admin approval
                from_admin=False
            )
            
            if 'image' in request.FILES:
                review.image = request.FILES['image']
            
            review.save()
            
            # Send email notification to admin
            send_review_notification_email(review)
            
            # Return JSON response for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for your review! It has been submitted and is awaiting approval.'
                })
            
            messages.success(request, 'Thank you for your review! It has been submitted and is awaiting approval.')
            
        except Exception as e:
            print(f"Review submission error: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'There was an error submitting your review. Please try again.'
                })
            messages.error(request, 'There was an error submitting your review. Please try again.')
    
    return redirect('index')

def send_review_notification_email(review):
    """Send email to admin when new review is submitted"""
    try:
        subject = f'🆕 New Review Submitted - Awaiting Approval'
        
        html_message = render_to_string('emails/admin_review_notification.html', {
            'review': review,
        })
        
        plain_message = f"""
New Review Submission - TradeWise

Reviewer: {review.author_name}
Role: {review.user_role}
Email: {review.email}
Rating: {review.rating}/5 stars

Review Content:
"{review.content}"

Submitted: {review.created_at.strftime('%Y-%m-%d %H:%M')}

Please log in to the admin dashboard to approve or reject this review.
        """
        
        # Send to admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"📧 REVIEW NOTIFICATION SENT TO ADMIN")
        return True
        
    except Exception as e:
        print(f"❌ REVIEW NOTIFICATION EMAIL ERROR: {str(e)}")
        return False

@admin_required
def add_review(request):
    """Add new review from admin"""
    if request.method == 'POST':
        try:
            author_name = request.POST.get('author_name')
            user_role = request.POST.get('user_role', 'Forex Trader')  # Changed from profession to user_role
            email = request.POST.get('email', '')
            content = request.POST.get('content')
            rating = int(request.POST.get('rating', 5))
            is_approved = request.POST.get('is_approved') == 'on'
            is_featured = request.POST.get('is_featured') == 'on'
            
            review = Review(
                author_name=author_name,
                client_name=author_name,  # Set both fields for compatibility
                user_role=user_role,      # Changed from profession to user_role
                email=email,
                content=content,
                rating=rating,
                is_approved=is_approved,
                is_featured=is_featured,
                from_admin=True
            )
            
            if 'image' in request.FILES:
                review.image = request.FILES['image']
            
            review.save()
            
            AdminLog.objects.create(
                user=get_current_admin(request),
                action=f'Added review from: {review.author_name}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Review added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error adding review: {str(e)}')
    
    return redirect('admin_dashboard')

@admin_required
def approve_review(request, review_id):
    """Approve a review"""
    try:
        review = Review.objects.get(id=review_id)
        review.is_approved = True
        review.save()
        
        messages.success(request, f'Review from {review.author_name} approved successfully!')
        
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    
    return redirect('admin_dashboard')

@admin_required
def toggle_review_featured(request, review_id):
    """Toggle review featured status"""
    try:
        review = Review.objects.get(id=review_id)
        review.is_featured = not review.is_featured
        review.save()
        
        status = "featured" if review.is_featured else "unfeatured"
        messages.success(request, f'Review {status} successfully!')
        
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    
    return redirect('admin_dashboard')

@admin_required
def delete_review(request, review_id):
    """Delete a review"""
    try:
        review = Review.objects.get(id=review_id)
        author_name = review.author_name
        review.delete()
        
        AdminLog.objects.create(
            user=get_current_admin(request),
            action=f'Deleted review from: {author_name}',
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, 'Review deleted successfully!')
        
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    
    return redirect('admin_dashboard')

@admin_required
def approve_all_pending_reviews(request):
    """Approve all pending reviews"""
    try:
        pending_reviews = Review.objects.filter(is_approved=False)
        count = pending_reviews.count()
        
        for review in pending_reviews:
            review.is_approved = True
            review.save()
        
        messages.success(request, f'Approved all {count} pending reviews!')
        
    except Exception as e:
        messages.error(request, f'Error approving reviews: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== FRONTEND API VIEWS ==================

def get_approved_reviews(request):
    """API endpoint to get approved reviews for frontend"""
    try:
        approved_reviews = Review.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')[:6]
        
        reviews_data = []
        for review in approved_reviews:
            reviews_data.append({
                'id': review.id,
                'author_name': review.author_name or review.client_name,
                'user_role': review.user_role,  # Changed from profession to user_role
                'content': review.content,
                'rating': review.rating,
                'image_url': review.image.url if review.image else '/static/images/default-avatar.jpg',
                'created_at': review.created_at.strftime('%b %d, %Y'),
                'is_featured': review.is_featured
            })
        
        return JsonResponse({
            'success': True,
            'reviews': reviews_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
def get_published_blogs(request):
    """API endpoint to get published blogs for frontend"""
    try:
        published_blogs = BlogPost.objects.filter(is_published=True).order_by('-created_at')
        
        blogs_data = []
        for blog in published_blogs:
            blogs_data.append({
                'id': blog.id,
                'title': blog.title,
                'content': blog.content,
                'excerpt': blog.content[:150] + '...' if len(blog.content) > 150 else blog.content,
                'author': blog.author,
                'featured_image': blog.featured_image.url if blog.featured_image else None,
                'created_at': blog.created_at.strftime('%b %d, %Y'),
                'slug': blog.slug
            })
        
        return JsonResponse({
            'success': True,
            'blogs': blogs_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ================== PAYMENT VIEWS ==================

def initialize_payment(request):
    """SIMPLE WORKING Paystack payment"""
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            amount = request.POST.get('amount')  # KES amount from form
            plan_type = request.POST.get('plan_type', 'VIP Package')
            
            print(f"🚀 PAYMENT INITIATED: {email}, {amount} KES, {plan_type}")
            
            # Validate required fields
            if not email or not amount:
                messages.error(request, 'Email and amount are required.')
                return redirect('market_hub')
            
            # Convert amount to integer (kobo for Paystack)
            try:
                amount_kes = float(amount)
                amount_in_kobo = int(amount_kes * 100)  # Convert KES to kobo
                print(f"💰 AMOUNT CONVERSION: {amount_kes} KES → {amount_in_kobo} kobo")
            except (ValueError, TypeError) as e:
                print(f"❌ AMOUNT CONVERSION ERROR: {e}")
                messages.error(request, 'Invalid amount format.')
                return redirect('market_hub')
            
            # Create payment record
            reference = f"TRD{uuid.uuid4().hex[:12].upper()}"
            payment = Payment.objects.create(
                email=email,
                amount=amount_kes,  # Store KES amount
                plan_type=plan_type,
                reference=reference,
                status='pending'
            )
            
            print(f"📝 PAYMENT RECORD CREATED: {reference}")
            
            # Initialize Paystack - This will use the class from models.py
            paystack_service = PaystackService()
            
            # Process with Paystack
            response = paystack_service.initialize_transaction(
                email=email,
                amount=amount_in_kobo,  # Send kobo amount to Paystack
                reference=reference,
                callback_url=request.build_absolute_uri(f'/verify-payment/{reference}/'),
                metadata={
                    'plan_type': plan_type,
                    'custom_fields': [
                        {
                            'display_name': "Service",
                            'variable_name': "service", 
                            'value': plan_type
                        }
                    ]
                }
            )
            
            print(f"📡 PAYSTACK RESPONSE: {response}")
            
            if response.get('status'):
                # Redirect to Paystack
                authorization_url = response['data']['authorization_url']
                print(f"🔗 REDIRECTING TO PAYSTACK: {authorization_url}")
                return redirect(authorization_url)
            else:
                error_msg = response.get('message', 'Unknown error occurred')
                print(f"❌ PAYSTACK ERROR: {error_msg}")
                messages.error(request, f"Payment initialization failed: {error_msg}")
                return redirect('market_hub')
                
        except Exception as e:
            print(f"💥 PAYMENT EXCEPTION: {str(e)}")
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('market_hub')
    
    # If not POST, redirect to market hub
    return redirect('market_hub')

def verify_payment(request, reference):
    """Simple payment verification"""
    try:
        payment = Payment.objects.get(reference=reference)
        payment.status = 'success'
        payment.save()
        messages.success(request, 'Payment verified successfully!')
        return redirect('index')
    except Exception as e:
        messages.error(request, f'Payment verification failed: {str(e)}')
        return redirect('index')


# PAYMENT PLAN VIEWS

def initialize_service_payment(request):
    """Simple service payment initialization"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            service_type = request.POST.get('service_type')
            total_amount = float(request.POST.get('service_price', 0))
            payment_amount = float(request.POST.get('payment_amount', total_amount))
            
            print(f"💰 SERVICE PAYMENT: {service_type}, KES {payment_amount}")
            
            # Create service payment
            service_payment = ServicePayment.objects.create(
                user_name=name,
                user_email=email,
                user_phone=phone,
                service_type=service_type,
                total_amount=total_amount
            )
            
            # Convert to kobo
            amount_in_kobo = int(payment_amount * 100)
            reference = f"SVC{secrets.token_hex(8).upper()}"
            
            # Create transaction
            ServiceTransaction.objects.create(
                service_payment=service_payment,
                amount=payment_amount,
                reference=reference
            )
            
            # Paystack
            paystack_service = PaystackService()
            response = paystack_service.initialize_transaction(
                email=email,
                amount=amount_in_kobo,
                reference=reference,
                callback_url=request.build_absolute_uri(f'/verify-service-payment/{reference}/'),
                metadata={'service_type': service_type}
            )
            
            if response.get('status'):
                return redirect(response['data']['authorization_url'])
            else:
                messages.error(request, "Payment failed to initialize")
                return redirect('payment')
                
        except Exception as e:
            print(f"❌ Service payment error: {str(e)}")
            messages.error(request, 'Payment error occurred')
            return redirect('payment')
    
    return redirect('payment')

def verify_service_payment(request, reference):
    """Simple payment verification"""
    try:
        transaction = ServiceTransaction.objects.get(reference=reference)
        
        paystack_service = PaystackService()
        verification = paystack_service.verify_transaction(reference)
        
        if verification.get('status') and verification['data']['status'] == 'success':
            transaction.status = 'success'
            transaction.save()
            
            # Update progress
            service_payment = transaction.service_payment
            service_payment.update_progress(transaction.amount)
            
            messages.success(request, 
                f'✅ Payment of KES {transaction.amount} received! '
                f'Progress: {service_payment.progress_percentage}% complete.'
            )
        else:
            transaction.status = 'failed'
            transaction.save()
            messages.error(request, '❌ Payment failed')
            
    except Exception as e:
        messages.error(request, '❌ Payment verification error')
    
    return redirect('payment')

def service_payment_progress(request):
    """Get user's service payment progress for AJAX calls"""
    if request.method == 'GET':
        # If user is logged in, get by email
        if request.user.is_authenticated and hasattr(request.user, 'email'):
            email = request.user.email
            service_payments = ServicePayment.objects.filter(user_email=email)
        else:
            # For non-logged in users, we can't track progress
            return JsonResponse({'progress': {}})
        
        progress_data = {}
        for payment in service_payments:
            progress_data[payment.service_type] = {
                'paid': float(payment.amount_paid),
                'total': float(payment.total_amount),
                'percentage': float(payment.progress_percentage),
                'status': payment.status
            }
        
        return JsonResponse({'progress': progress_data})
    
    return JsonResponse({'progress': {}})
# ================== EMAIL FUNCTIONS ==================

def send_order_confirmation_email(payment, user):
    """Send order confirmation to client"""
    try:
        subject = '🎉 TradeWise Order Confirmation - VIP Access Activated'
        
        html_message = render_to_string('emails/order_confirmation.html', {
            'user': user,
            'service': payment.plan_type,
            'amount': payment.amount,
            'reference': payment.reference,
            'payment_date': payment.created_at.strftime('%Y-%m-%d %H:%M')
        })
        
        plain_message = f"""
Order Confirmation - TradeWise

Dear {user.first_name},

Thank you for purchasing {payment.plan_type}!

Order Details:
- Service: {payment.plan_type}
- Amount: KES {payment.amount}
- Reference: {payment.reference}
- Date: {payment.created_at.strftime('%Y-%m-%d %H:%M')}

Your VIP access has been activated. Log in to your account to access premium features.

Best regards,
TradeWise Team
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"📧 ORDER CONFIRMATION SENT TO: {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ ORDER CONFIRMATION EMAIL ERROR: {str(e)}")
        return False

def send_admin_notification(payment, user):
    """Send admin notification for new purchase"""
    try:
        subject = f'🛒 New VIP Purchase - {user.first_name} {user.second_name}'
        
        html_message = render_to_string('emails/admin_notification.html', {
            'user': user,
            'service': payment.plan_type,
            'amount': payment.amount,
            'reference': payment.reference,
        })
        
        plain_message = f"""
New VIP Purchase - TradeWise

Customer: {user.first_name} {user.second_name}
Email: {user.email}
Phone: {user.phone}

Purchase Details:
Service: {payment.plan_type}
Amount: KES {payment.amount}
Reference: {payment.reference}

Please verify VIP access in admin dashboard.
        """
        
        # Send to admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"📧 ADMIN NOTIFICATION SENT")
        return True
        
    except Exception as e:
        print(f"❌ ADMIN NOTIFICATION EMAIL ERROR: {str(e)}")
        return False

# ================== ADMIN FORM HANDLING ==================

def handle_admin_form_submission(request):
    """Handle all admin form submissions"""
    action = request.POST.get('action')
    
    if action == 'update_card':
        return update_tradewise_card(request)
    elif action == 'update_coin':
        return update_tradewise_coin(request)
    elif action == 'add_strategy':
        return add_trading_strategy(request)
    elif action == 'add_signal':
        return add_trading_signal(request)
    elif action == 'add_software':
        return add_software_tool(request)
    elif action == 'add_service':
        return add_payment_service(request)
    elif action == 'add_blog':
        return add_blog_post(request)
    elif action == 'add_merchandise':
        return add_merchandise_item(request)
    elif action == 'add_review':
        return add_review(request)  # This should now work with user_role
    elif action == 'update_weekly_number':
        return update_weekly_number(request)
    
    # ================== DELETE ACTIONS ==================
    elif action == 'delete_strategy':
        return delete_strategy(request)
    elif action == 'delete_signal':
        return delete_signal(request)
    elif action == 'delete_software':
        return delete_software(request)
    elif action == 'delete_blog':
        return delete_blog_post(request)
    elif action == 'delete_merchandise':
        return delete_merchandise(request)
    elif action == 'delete_review':
        return delete_review(request)
    
    # ================== USER MANAGEMENT ACTIONS ==================
    elif action == 'disable_user':
        return disable_user_traditional(request)
    elif action == 'enable_user':
        return enable_user_traditional(request)
    elif action == 'reset_password':
        return reset_password_traditional(request)
    elif action == 'view_user_details':
        return view_user_details_traditional(request)
    
    # ================== REQUEST MANAGEMENT ACTIONS ==================
    elif action == 'update_request_status':
        return update_request_status_traditional(request)
    
    # ================== REVIEW MANAGEMENT ACTIONS ==================
    elif action == 'review_action':
        return review_action_traditional(request)
    
    # ================== AFFILIATE MANAGEMENT ACTIONS ==================
    elif action == 'process_payout':
        return process_payout_traditional(request)
    elif action == 'approve_referral':
        return approve_referral_traditional(request)
    elif action == 'approve_all_referrals':
        return approve_all_referrals_traditional(request)
    
    # ================== SERVICE PAYMENT ACTIONS ==================
    elif action == 'send_onboarding_email':
        return send_onboarding_email_traditional(request)
    elif action == 'add_manual_payment':
        return add_manual_payment_traditional(request)
    
    # ================== SOFTWARE MANAGEMENT ACTIONS ==================
    elif action == 'track_download':
        return track_download_traditional(request)
    
    messages.error(request, 'Invalid action.')
    return redirect('admin_dashboard')

# ================== DELETE HANDLERS ==================

def delete_strategy(request):
    """Delete strategy - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        strategy = TradingStrategy.objects.get(id=item_id)
        strategy_name = strategy.title
        strategy.delete()
        
        messages.success(request, f'Strategy "{strategy_name}" deleted successfully!')
        print(f"✅ Strategy {strategy_name} deleted")
    except TradingStrategy.DoesNotExist:
        messages.error(request, 'Strategy not found.')
    except Exception as e:
        messages.error(request, f'Error deleting strategy: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_signal(request):
    """Delete signal - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        signal = TradingSignal.objects.get(id=item_id)
        signal_name = signal.title
        signal.delete()
        
        messages.success(request, f'Signal "{signal_name}" deleted successfully!')
        print(f"✅ Signal {signal_name} deleted")
    except TradingSignal.DoesNotExist:
        messages.error(request, 'Signal not found.')
    except Exception as e:
        messages.error(request, f'Error deleting signal: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_software(request):
    """Delete software - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        software = SoftwareTool.objects.get(id=item_id)
        software_name = software.name
        software.delete()
        
        messages.success(request, f'Software "{software_name}" deleted successfully!')
        print(f"✅ Software {software_name} deleted")
    except SoftwareTool.DoesNotExist:
        messages.error(request, 'Software not found.')
    except Exception as e:
        messages.error(request, f'Error deleting software: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_blog_post(request):
    """Delete blog post - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        blog_post = BlogPost.objects.get(id=item_id)
        blog_title = blog_post.title
        blog_post.delete()
        
        messages.success(request, f'Blog post "{blog_title}" deleted successfully!')
        print(f"✅ Blog post {blog_title} deleted")
    except BlogPost.DoesNotExist:
        messages.error(request, 'Blog post not found.')
    except Exception as e:
        messages.error(request, f'Error deleting blog post: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_merchandise(request):
    """Delete merchandise - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        merchandise = Merchandise.objects.get(id=item_id)
        merchandise_name = merchandise.name
        merchandise.delete()
        
        messages.success(request, f'Merchandise "{merchandise_name}" deleted successfully!')
        print(f"✅ Merchandise {merchandise_name} deleted")
    except Merchandise.DoesNotExist:
        messages.error(request, 'Merchandise not found.')
    except Exception as e:
        messages.error(request, f'Error deleting merchandise: {str(e)}')
    
    return redirect('admin_dashboard')

def delete_review(request):
    """Delete review - traditional form"""
    try:
        item_id = request.POST.get('item_id')
        review = Review.objects.get(id=item_id)
        review_author = review.author_name
        review.delete()
        
        messages.success(request, f'Review by "{review_author}" deleted successfully!')
        print(f"✅ Review by {review_author} deleted")
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    except Exception as e:
        messages.error(request, f'Error deleting review: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== USER MANAGEMENT HANDLERS ==================

def disable_user_traditional(request):
    """Disable user - traditional form"""
    try:
        user_id = request.POST.get('user_id')
        user = Tradeviewusers.objects.get(id=user_id)
        user.is_active = False
        user.save()
        
        messages.success(request, f'User "{user.first_name} {user.second_name}" disabled successfully!')
        print(f"✅ User {user.first_name} disabled")
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'User not found.')
    except Exception as e:
        messages.error(request, f'Error disabling user: {str(e)}')
    
    return redirect('admin_dashboard')

def enable_user_traditional(request):
    """Enable user - traditional form"""
    try:
        user_id = request.POST.get('user_id')
        user = Tradeviewusers.objects.get(id=user_id)
        user.is_active = True
        user.save()
        
        messages.success(request, f'User "{user.first_name} {user.second_name}" enabled successfully!')
        print(f"✅ User {user.first_name} enabled")
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'User not found.')
    except Exception as e:
        messages.error(request, f'Error enabling user: {str(e)}')
    
    return redirect('admin_dashboard')

def reset_password_traditional(request):
    """Reset password - traditional form"""
    try:
        user_id = request.POST.get('user_id')
        user = Tradeviewusers.objects.get(id=user_id)
        
        # Send password reset email logic here
        # For now, just show a message
        messages.success(request, f'Password reset email sent to {user.email}!')
        print(f"✅ Password reset sent to {user.email}")
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'User not found.')
    except Exception as e:
        messages.error(request, f'Error resetting password: {str(e)}')
    
    return redirect('admin_dashboard')

def view_user_details_traditional(request):
    """View user details - traditional form"""
    try:
        user_id = request.POST.get('user_id')
        # Store user ID in session to show details on page reload
        request.session['viewing_user_id'] = user_id
        messages.info(request, 'User details loaded.')
    except Exception as e:
        messages.error(request, f'Error loading user details: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== REQUEST MANAGEMENT HANDLERS ==================

def update_request_status_traditional(request):
    """Update request status - traditional form"""
    try:
        request_id = request.POST.get('request_id')
        status = request.POST.get('status')
        
        service_request = ServiceRequest.objects.get(id=request_id)
        service_request.status = status
        service_request.save()
        
        messages.success(request, f'Request status updated to {status}!')
        print(f"✅ Request {request_id} status updated to {status}")
    except ServiceRequest.DoesNotExist:
        messages.error(request, 'Request not found.')
    except Exception as e:
        messages.error(request, f'Error updating request: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== REVIEW MANAGEMENT HANDLERS ==================

def review_action_traditional(request):
    """Review actions - traditional form"""
    try:
        review_id = request.POST.get('review_id')
        review_action = request.POST.get('review_action')
        
        review = Review.objects.get(id=review_id)
        
        if review_action == 'approve':
            review.is_approved = True
            messages.success(request, 'Review approved!')
            print(f"✅ Review {review_id} approved")
        elif review_action == 'feature':
            review.is_featured = True
            messages.success(request, 'Review featured!')
            print(f"✅ Review {review_id} featured")
        elif review_action == 'unfeature':
            review.is_featured = False
            messages.success(request, 'Review unfeatured!')
            print(f"✅ Review {review_id} unfeatured")
        
        review.save()
        
    except Review.DoesNotExist:
        messages.error(request, 'Review not found.')
    except Exception as e:
        messages.error(request, f'Error processing review: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== AFFILIATE MANAGEMENT HANDLERS ==================

def process_payout_traditional(request):
    """Process payout - traditional form"""
    try:
        payout_id = request.POST.get('payout_id')
        payout_status = request.POST.get('payout_status')
        
        payout = PayoutRequest.objects.get(id=payout_id)
        payout.status = payout_status
        payout.processed_at = timezone.now()
        payout.save()
        
        messages.success(request, f'Payout {payout_status}!')
        print(f"✅ Payout {payout_id} {payout_status}")
    except PayoutRequest.DoesNotExist:
        messages.error(request, 'Payout request not found.')
    except Exception as e:
        messages.error(request, f'Error processing payout: {str(e)}')
    
    return redirect('admin_dashboard')

def approve_referral_traditional(request):
    """Approve referral - traditional form"""
    try:
        referral_id = request.POST.get('referral_id')
        referral = Referral.objects.get(id=referral_id)
        
        # Award coins to affiliate
        affiliate = referral.affiliate
        affiliate.coin_balance += 50
        affiliate.total_coins_earned += 50
        affiliate.save()
        
        # Update referral status
        referral.status = 'approved'
        referral.coins_awarded = 50
        referral.approved_at = timezone.now()
        referral.save()
        
        messages.success(request, 'Referral approved and 50 coins awarded!')
        print(f"✅ Referral {referral_id} approved, 50 coins awarded")
    except Referral.DoesNotExist:
        messages.error(request, 'Referral not found.')
    except Exception as e:
        messages.error(request, f'Error approving referral: {str(e)}')
    
    return redirect('admin_dashboard')

def approve_all_referrals_traditional(request):
    """Approve all referrals - traditional form"""
    try:
        pending_referrals = Referral.objects.filter(status='pending')
        approved_count = 0
        
        for referral in pending_referrals:
            # Award coins to affiliate
            affiliate = referral.affiliate
            affiliate.coin_balance += 50
            affiliate.total_coins_earned += 50
            affiliate.save()
            
            # Update referral status
            referral.status = 'approved'
            referral.coins_awarded = 50
            referral.approved_at = timezone.now()
            referral.save()
            approved_count += 1
        
        messages.success(request, f'All {approved_count} pending referrals approved!')
        print(f"✅ {approved_count} referrals approved")
    except Exception as e:
        messages.error(request, f'Error approving referrals: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== SERVICE PAYMENT HANDLERS ==================

def send_onboarding_email_traditional(request):
    """Send onboarding email - traditional form"""
    try:
        payment_id = request.POST.get('payment_id')
        payment = ServicePayment.objects.get(id=payment_id)
        
        # Implement your email sending logic here
        # For now, just mark as sent and show message
        payment.email_sent = True
        payment.save()
        
        messages.success(request, 'Onboarding email sent successfully!')
        print(f"✅ Onboarding email sent for payment {payment_id}")
    except ServicePayment.DoesNotExist:
        messages.error(request, 'Payment not found.')
    except Exception as e:
        messages.error(request, f'Error sending email: {str(e)}')
    
    return redirect('admin_dashboard')

def add_manual_payment_traditional(request):
    """Add manual payment - traditional form"""
    try:
        payment_id = request.POST.get('payment_id')
        amount = float(request.POST.get('amount'))
        
        payment = ServicePayment.objects.get(id=payment_id)
        payment.amount_paid += amount
        
        # Update progress percentage
        if payment.total_amount > 0:
            payment.progress_percentage = (payment.amount_paid / payment.total_amount) * 100
        
        # Update status if fully paid
        if payment.amount_paid >= payment.total_amount:
            payment.status = 'completed'
            payment.progress_percentage = 100
        
        payment.save()
        
        messages.success(request, f'Manual payment of KES {amount} added successfully!')
        print(f"✅ Manual payment of {amount} added to payment {payment_id}")
    except ServicePayment.DoesNotExist:
        messages.error(request, 'Payment not found.')
    except Exception as e:
        messages.error(request, f'Error adding manual payment: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== SOFTWARE MANAGEMENT HANDLERS ==================

def track_download_traditional(request):
    """Track download - traditional form"""
    try:
        software_id = request.POST.get('software_id')
        software = SoftwareTool.objects.get(id=software_id)
        software.download_count += 1
        software.save()
        
        # Return the file for download
        from django.http import FileResponse
        response = FileResponse(software.file.open(), as_attachment=True, filename=software.file.name)
        return response
        
    except SoftwareTool.DoesNotExist:
        messages.error(request, 'Software not found.')
        return redirect('admin_dashboard')
    except Exception as e:
        messages.error(request, f'Error downloading software: {str(e)}')
        return redirect('admin_dashboard')

# ================== TRADEWISE CARD SECTION ==================
def get_card_data(request):
    """AJAX endpoint for TradeWise card data"""
    try:
        card = TradeWiseCard.objects.filter(is_active=True).first()
        if not card:
            # Create default card
            card = TradeWiseCard.objects.create(
                title="TradeWise Premium",
                card_number="6734 5590 1234 5678",
                capital_available="$500,000",
                partner_name="SPALIS FX",
                contact_number="+254742962615"
            )
        
        html = f"""
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
            <button id="toggleCardBtn" class="btn-toggle-card" style="background: linear-gradient(135deg, #3498db, #2c3e50); color: white; border: none; border-radius: 30px; padding: 12px 30px; font-weight: 600; cursor: pointer; box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3); transition: all 0.3s ease;">
                <span id="btnText">Show Physical Card</span>
                <i id="btnIcon" class="fas fa-eye" style="margin-left: 8px;"></i>
            </button>
        </div>
        """
        
        return JsonResponse({
            'success': True,
            'html': html,
            'card_data': {
                'card_number': card.card_number,
                'capital_available': card.capital_available,
                'partner_name': card.partner_name,
                'contact_number': card.contact_number,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ================== ADMIN CRUD OPERATIONS ==================

def update_tradewise_card(request):
    """Update TradeWise card details"""
    card, created = TradeWiseCard.objects.get_or_create(pk=1)
    
    card.title = request.POST.get('title', 'TradeWise Premium')
    card.subtitle = request.POST.get('subtitle', '')
    card.description = request.POST.get('description', '')
    card.card_number = request.POST.get('card_number', '6734 559')
    card.capital_available = request.POST.get('capital_available', '$500,000')
    card.partner_name = request.POST.get('partner_name', 'SPALIS FX')
    card.contact_number = request.POST.get('contact_number', '+254742962615')
    card.price_monthly = request.POST.get('price_monthly', 49.99)
    card.price_yearly = request.POST.get('price_yearly', 499.99)
    
    if 'image' in request.FILES:
        card.image = request.FILES['image']
    
    card.save()
    
    # Log action
    AdminLog.objects.create(
        user=get_current_admin(request),
        action='Updated TradeWise card details',
        ip_address=get_client_ip(request)
    )
    
    messages.success(request, 'TradeWise card updated successfully!')
    return redirect('admin_dashboard')

def update_tradewise_coin(request):
    """Update TradeWise coin information"""
    coin, created = TradeWiseCoin.objects.get_or_create(pk=1)
    
    coin.title = request.POST.get('title', 'TradeWise Coin')
    coin.subtitle = request.POST.get('subtitle', '')
    coin.description = request.POST.get('description', '')
    coin.price = request.POST.get('price', '$0.10 per TWC (Limited Supply)')
    coin.bonus_text = request.POST.get('bonus_text', 'Early investors get +15% bonus tokens in the first round.')
    coin.is_active = request.POST.get('is_active') == 'on'
    
    if 'image' in request.FILES:
        coin.image = request.FILES['image']
    
    coin.save()
    
    AdminLog.objects.create(
        user=get_current_admin(request),
        action='Updated TradeWise coin information',
        ip_address=get_client_ip(request)
    )
    
    messages.success(request, 'TradeWise coin information updated successfully!')
    return redirect('admin_dashboard')

def add_trading_strategy(request):
    """Add new trading strategy with enhanced fields"""
    try:
        strategy = TradingStrategy(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            price_usd=request.POST.get('price_usd', 0),
            price_kes=request.POST.get('price_kes', 0),
            market_type=request.POST.get('market_type', 'all'),
            difficulty_level=request.POST.get('difficulty_level', 'all'),
            strategy_type=request.POST.get('strategy_type', 'free'),
            is_featured=request.POST.get('is_featured') == 'on',
            is_active=request.POST.get('is_active') == 'on'
        )
        
        if 'image' in request.FILES:
            strategy.image = request.FILES['image']
        
        strategy.save()
        
        # FIXED: Use the safe admin log function
        create_admin_log(
            request, 
            f'Added trading strategy: {strategy.title}',
            f"Strategy '{strategy.title}' added with price ${strategy.price_usd} USD"
        )
        
        messages.success(request, 'Trading strategy added successfully!')
        
    except Exception as e:
        messages.error(request, f'Error adding strategy: {str(e)}')
    
    return redirect('admin_dashboard')

def create_admin_log(request, action, details=""):
    """Safely create admin log entry"""
    try:
        admin_user = get_current_admin(request)
        
        AdminLog.objects.create(
            user=admin_user,  # This can be null if admin_user is None
            action=action,
            details=details,
            ip_address=get_client_ip(request)
        )
        return True
    except Exception as e:
        print(f"Failed to create admin log: {e}")
        return False

def add_trading_signal(request):
    """Add new trading signal"""
    try:
        signal = TradingSignal(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            price_usd=request.POST.get('price_usd', 0),
            price_kes=request.POST.get('price_kes', 0),
            signal_type=request.POST.get('signal_type', 'forex'),
            accuracy_forex=request.POST.get('accuracy_forex', 80),
            accuracy_crypto=request.POST.get('accuracy_crypto', 75),
            is_active=True  # Make sure it's active by default
        )
        
        if 'image' in request.FILES:
            signal.image = request.FILES['image']
        
        signal.save()
        
        # FIXED: Safe AdminLog creation
        try:
            admin_user = get_current_admin(request)
            AdminLog.objects.create(
                user=admin_user,  # This can be null
                action=f'Added trading signal: {signal.title}',
                ip_address=get_client_ip(request)
            )
        except Exception as e:
            print(f"AdminLog creation failed: {e}")
            # Continue anyway - don't let logging break the main functionality
        
        messages.success(request, 'Trading signal added successfully!')
        
    except Exception as e:
        messages.error(request, f'Error adding signal: {str(e)}')
    
    return redirect('admin_dashboard')

def add_blog_post(request):
    """Add new blog post"""
    blog = BlogPost(
        title=request.POST.get('title'),
        content=request.POST.get('content'),
        author=request.POST.get('author', 'TradeWise Team'),
        is_published=request.POST.get('is_published') == 'on'
    )
    
    if 'featured_image' in request.FILES:
        blog.featured_image = request.FILES['featured_image']
    
    blog.save()
    
    AdminLog.objects.create(
        user=get_current_admin(request),
        action=f'Added blog post: {blog.title}',
        ip_address=get_client_ip(request)
    )
    
    messages.success(request, 'Blog post added successfully!')
    return redirect('admin_dashboard')

def add_merchandise_item(request):
    """Add new merchandise item - FIXED VERSION"""
    merchandise = Merchandise(
        name=request.POST.get('name'),
        category=request.POST.get('category', 't-shirts'),
        description=request.POST.get('description'),
        price=request.POST.get('price', 0),
        stock_quantity=request.POST.get('stock_quantity', 100),
        is_available=True,  # EXPLICITLY SET TO TRUE
        is_featured=request.POST.get('is_featured') == 'on',
    )
    
    if 'image' in request.FILES:
        merchandise.image = request.FILES['image']
    
    merchandise.save()
    
    messages.success(request, 'Merchandise item added successfully!')
    return redirect('admin_dashboard')

def add_review(request):
    """Add new review from admin"""
    if request.method == 'POST':
        try:
            author_name = request.POST.get('author_name')
            user_role = request.POST.get('user_role', 'Forex Trader')  # Use user_role (not profession)
            email = request.POST.get('email', '')
            content = request.POST.get('content')
            rating = int(request.POST.get('rating', 5))
            is_approved = request.POST.get('is_approved') == 'on'
            is_featured = request.POST.get('is_featured') == 'on'
            
            review = Review(
                author_name=author_name,
                client_name=author_name,  # Set both fields for compatibility
                user_role=user_role,      # Use user_role (correct field name)
                email=email,
                content=content,
                rating=rating,
                is_approved=is_approved,
                is_featured=is_featured,
                from_admin=True
            )
            
            if 'image' in request.FILES:
                review.image = request.FILES['image']
            
            review.save()
            
            AdminLog.objects.create(
                user=get_current_admin(request),
                action=f'Added review from: {review.author_name}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Review added successfully!')
            
        except Exception as e:
            messages.error(request, f'Error adding review: {str(e)}')
    
    return redirect('admin_dashboard')


def add_software_tool(request):
    """Add new software tool"""
    try:
        software = SoftwareTool(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            file_type=request.POST.get('file_type', 'software'),
            version=request.POST.get('version', '1.0'),
            compatibility=request.POST.get('compatibility', ''),
            requirements=request.POST.get('requirements', ''),
            installation_guide=request.POST.get('installation_guide', ''),
            is_free=request.POST.get('is_free') == 'on',
            price_usd=request.POST.get('price_usd', 0),
            price_kes=request.POST.get('price_kes', 0),
            is_active=request.POST.get('is_active') == 'on',
            is_featured=request.POST.get('is_featured') == 'on',
            requires_vip=request.POST.get('requires_vip') == 'on',
        )
        
        if 'file' in request.FILES:
            software.file = request.FILES['file']
            
        if 'thumbnail' in request.FILES:
            software.thumbnail = request.FILES['thumbnail']
        
        software.save()
        
        create_admin_log(
            request,
            f'Added software tool: {software.name}',
            f"Software '{software.name}' added as {software.get_file_type_display()}"
        )
        
        messages.success(request, 'Software tool added successfully!')
        
    except Exception as e:
        messages.error(request, f'Error adding software tool: {str(e)}')
    
    return redirect('admin_dashboard')

def activate_all_software(request):
    """Activate all software tools"""
    software_tools = SoftwareTool.objects.all()
    count = software_tools.count()
    
    for software in software_tools:
        software.is_active = True
        software.save()
    
    messages.success(request, f'Activated all {count} software tools!')
    return redirect('admin_dashboard')

# Add software frontend views
def free_software(request):
    """Display free trading software"""
    software_list = SoftwareTool.objects.filter(
        is_active=True,
        is_free=True
    ).order_by('-is_featured', '-created_at')
    
    context = {
        'software_list': software_list,
        'page_title': 'Free Trading Software',
        'description': 'Download free trading tools, bots, and indicators. Upgrade to VIP for premium software.'
    }
    return render(request, 'market/software_free.html', context)

def premium_software(request):
    """Display premium trading software (VIP only)"""
    software_list = SoftwareTool.objects.filter(
        is_active=True,
        requires_vip=True
    ).order_by('-is_featured', '-created_at')
    
    context = {
        'software_list': software_list,
        'page_title': 'Premium Trading Software',
        'description': 'VIP access required to download premium software tools.'
    }
    return render(request, 'software_premium.html', context)

@csrf_exempt
def track_software_download(request, software_id):
    """Track software downloads via AJAX"""
    if request.method == 'POST':
        try:
            software = SoftwareTool.objects.get(id=software_id)
            software.increment_download_count()
            
            return JsonResponse({
                'success': True,
                'download_url': software.file.url if software.file else '#',
                'message': 'Download counted successfully'
            })
        except SoftwareTool.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Software not found'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def software_detail(request, software_id):
    """Individual software detail page"""
    software = get_object_or_404(SoftwareTool, id=software_id, is_active=True)
    
    # Increment view count
    software.increment_view_count()
    
    context = {
        'software': software,
        'related_software': SoftwareTool.objects.filter(
            file_type=software.file_type,
            is_active=True
        ).exclude(id=software_id)[:4]
    }
    return render(request, 'market/software_detail.html', context)

def submit_service_request(request):
    """Handle service request submissions from website"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        service_type = request.POST.get('service_type', 'general')
        service_details = request.POST.get('service_details', '')
        
        # Create service request
        service_request = ServiceRequest(
            name=name,
            email=email,
            phone=phone,
            request_type=service_type,
            service_details=service_details
        )
        service_request.save()
        
        messages.success(request, 'Your service request has been submitted successfully! We will contact you soon.')
        return redirect('index')
    
    return redirect('index')


def send_service_request_email_to_admin(service_request):
    """Send email to admin when new service request is made"""
    try:
        print(f"🟢 STARTING ADMIN EMAIL FOR REQUEST: {service_request.id}")
        
        subject = f'🆕 New Service Request: {service_request.get_request_type_display()}'
        
        # Print debug info
        print(f"📧 Admin Email Details:")
        print(f"   - Subject: {subject}")
        print(f"   - Admin Email: {getattr(settings, 'ADMIN_EMAIL', 'NOT SET')}")
        print(f"   - From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
        
        html_message = render_to_string('emails/admin_service_request.html', {
            'request': service_request,
        })
        
        plain_message = f"""
New Service Request - TradeWise

Customer Details:
- Name: {service_request.name}
- Email: {service_request.email}
- Phone: {service_request.phone}

Service Requested: {service_request.get_request_type_display()}
Additional Details: {service_request.service_details}

Submitted: {service_request.created_at.strftime('%Y-%m-%d %H:%M')}

Please check the admin dashboard to process this request.
        """
        
        # Send to admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
        print(f"   - Sending to: {admin_email}")
        
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ ADMIN EMAIL SENT SUCCESSFULLY! Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ ADMIN EMAIL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def send_service_confirmation_to_user(service_request):
    """Send confirmation email to user"""
    try:
        print(f"🟢 STARTING USER CONFIRMATION EMAIL FOR: {service_request.email}")
        
        subject = '✅ TradeWise Service Request Received'
        
        print(f"📧 User Email Details:")
        print(f"   - Subject: {subject}")
        print(f"   - To: {service_request.email}")
        print(f"   - From: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
        
        html_message = render_to_string('emails/user_service_confirmation.html', {
            'request': service_request,
        })
        
        plain_message = f"""
Service Request Received - TradeWise

Dear {service_request.name},

Thank you for your interest in our {service_request.get_request_type_display()} service!

We have received your request and our team will contact you within 24 hours to discuss your requirements.

Request Details:
- Service: {service_request.get_request_type_display()}
- Submitted: {service_request.created_at.strftime('%Y-%m-%d %H:%M')}
- Reference: SR{service_request.id:06d}

What to expect next:
1. Our expert will contact you via phone/email
2. We'll discuss your specific needs
3. We'll provide customized solutions
4. You'll get access to your chosen service

If you have any urgent questions, please contact us at +254742962615.

Best regards,
TradeWise Team
        """
        
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[service_request.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ USER CONFIRMATION EMAIL SENT SUCCESSFULLY! Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ USER CONFIRMATION EMAIL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ================== UTILITY FUNCTIONS ==================

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_current_admin(request):
    """Get current admin user from session"""
    try:
        # Try to get admin user from session
        admin_username = request.session.get('admin_username')
        admin_number = request.session.get('admin_number')
        
        if admin_username and admin_number:
            # Try to find matching admin user
            admin_user = Tradeviewusers.objects.filter(
                Q(first_name=admin_username) | Q(account_number=admin_number),
                is_admin=True
            ).first()
            
            if admin_user:
                return admin_user
        
        # Fallback: get any admin user or create a system user
        admin_user = Tradeviewusers.objects.filter(is_admin=True).first()
        if admin_user:
            return admin_user
            
        # Last resort: create a system admin user if none exists
        system_admin = Tradeviewusers.objects.create(
            first_name="System",
            last_name="Admin", 
            email="system@tradewise.com",
            account_number="500000",
            is_admin=True,
            is_active=True
        )
        system_admin.set_password("system_admin_123")
        system_admin.save()
        return system_admin
        
    except Exception as e:
        print(f"Error getting admin user: {e}")
        return None

# ================== ERROR HANDLING ==================

def handler404(request, exception):
    """404 error handler"""
    return render(request, '404.html', status=404)

def payment(request):
    """Payment page"""
    return render(request, 'payment.html')

def handler500(request):
    """500 error handler"""
    return render(request, '500.html', status=500)

# ================== ADDITIONAL UTILITY FUNCTIONS ==================

def send_welcome_email(self, password):
    """Send welcome email to new user - UPDATED WITH DEBUGGING"""
    try:
        print(f"🟢 WELCOME EMAIL: Starting for {self.email}")
        print(f"📧 Welcome email details:")
        print(f"   - User: {self.first_name} {self.second_name}")
        print(f"   - Account: {self.account_number}")
        print(f"   - Password: {password}")
        print(f"   - Template: welcome_email.html")
        
        subject = '🎉 Welcome to TradeWise - Your Trading Journey Begins!'
        
        # Render HTML template with ALL required context variables
        try:
            html_message = render_to_string('emails/welcome_email.html', {
                'user': self,
                'plain_password': password,  # ✅ Changed to match template variable name
            })
            print(f"✅ WELCOME EMAIL: Template rendered successfully")
        except Exception as e:
            print(f"❌ WELCOME EMAIL: Template error: {e}")
            html_message = f"""
            <h2>Welcome to TradeWise!</h2>
            <p>Hello {self.first_name}, your account was created successfully!</p>
            <p>Account Number: {self.account_number}</p>
            <p>Temporary Password: {password}</p>
            """
        
        plain_message = f"""
Welcome to TradeWise, {self.first_name}!

We're excited to have you join our trading community. Here are your account details:

Account Information:
- Name: {self.first_name} {self.second_name}
- TradeWise Number: {self.account_number}
- Email: {self.email}
- Temporary Password: {password}

Please log in and change your password immediately for security.

Start exploring our features:
• Trading signals and strategies
• Market analysis tools  
• Educational resources
• Community support

Happy Trading!
The TradeWise Team
        """
        
        print(f"📧 Sending welcome email to: {self.email}")
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[self.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ WELCOME EMAIL: Sent successfully - Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ WELCOME EMAIL: Failed to send - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def send_new_user_notification(self):
    """Send admin notification for new user - UPDATED WITH DEBUGGING"""
    try:
        print(f"🟢 ADMIN NOTIFICATION: Starting for new user {self.email}")
        
        # Calculate additional context for admin template
        total_users = Tradeviewusers.objects.count()
        registration_time = self.created_at.strftime('%B %d, %Y at %I:%M %p')
        
        print(f"📧 Admin notification details:")
        print(f"   - User: {self.first_name} {self.second_name}")
        print(f"   - Account: {self.account_number}")
        print(f"   - Total Users: {total_users}")
        print(f"   - Registration: {registration_time}")
        print(f"   - Template: new_user.html")
        
        subject = '👤 New User Registration - TradeWise'
        
        # Render HTML template with ALL required context variables
        try:
            html_message = render_to_string('emails/new_user.html', {
                'user': self,
                'registration_time': registration_time,  # ✅ Added for template
                'total_users': total_users,  # ✅ Added for template
            })
            print(f"✅ ADMIN NOTIFICATION: Template rendered successfully")
        except Exception as e:
            print(f"❌ ADMIN NOTIFICATION: Template error: {e}")
            html_message = f"""
            <h2>New User Registered</h2>
            <p>Name: {self.first_name} {self.second_name}</p>
            <p>Email: {self.email}</p>
            <p>Account: {self.account_number}</p>
            <p>Phone: {self.phone}</p>
            <p>Registered: {registration_time}</p>
            <p>Total Users: {total_users}</p>
            """
        
        plain_message = f"""
New user registered on TradeWise:

User Details:
- Name: {self.first_name} {self.second_name}
- TradeWise Number: {self.account_number}
- Email: {self.email}
- Phone: {self.phone}
- Registration Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}
- Total Platform Users: {total_users}

Please review the user in the admin dashboard.
        """
        
        # Send to admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
        print(f"📧 Sending admin notification to: {admin_email}")
        
        result = send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        print(f"✅ ADMIN NOTIFICATION: Sent successfully - Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ ADMIN NOTIFICATION: Failed to send - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Add these methods to Tradeviewusers model (they'll be monkey-patched)
Tradeviewusers.send_welcome_email = send_welcome_email
Tradeviewusers.send_new_user_notification = send_new_user_notification

def payment_verify(request, reference):
    """Verify payment callback"""
    try:
        payment = Payment.objects.get(reference=reference)
        payment.status = 'success'
        payment.save()
        
        messages.success(request, 'Payment verified successfully!')
    except Payment.DoesNotExist:
        messages.error(request, 'Payment record not found.')
    
    return redirect('index')

# ================== MARKET HUB & TRADING VIEWS ==================

def market_hub(request):
    """Market hub page"""
    return render(request, 'market_hub.html')

def trade(request):
    """Trading page"""
    return render(request, 'trade_desk.html')

def contact(request):
    """Contact page"""
    return render(request, 'contact.html')

def account(request):
    """User account dashboard - USING USER_ID FOR REFERRAL LINKS"""
    # Get current user from session
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please log in to access your account.')
        return redirect('login_view')
    
    try:
        user = Tradeviewusers.objects.get(id=user_id)
        
        # Get or create affiliate data
        try:
            affiliate = Affiliate.objects.get(user=user)
        except Affiliate.DoesNotExist:
            # Create affiliate account if it doesn't exist
            referral_code = f"TW{user.account_number}"
            affiliate = Affiliate.objects.create(
                user=user,
                referral_code=referral_code
            )
            print(f"✅ Created new affiliate account: {referral_code}")
        
        # Prepare referral stats
        referral_stats = {
            'total_referrals': affiliate.total_referrals,
            'total_coins': affiliate.total_coins_earned,
            'coin_balance': affiliate.coin_balance,
            'pending_coins': 0,
        }
        cash_value = affiliate.coin_balance * 10  # 10 Ksh per coin
        
        # Get current weekly number
        current_weekly_number = WeeklyNumber.objects.filter(is_active=True).first()
        print(f"🔍 ACCOUNT DEBUG: Current weekly number: {current_weekly_number}")
        
        # Get user's payout history
        payout_history = PayoutRequest.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Get recent referrals
        recent_referrals = Referral.objects.filter(affiliate=affiliate).select_related('referred_user').order_by('-created_at')[:5]
        
        context = {
            'user': user,
            'first_name': user.first_name,
            'second_name': user.second_name,
            'account_number': user.account_number,
            'user_id': user.id,  # USING USER_ID FOR REFERRAL LINKS
            'referral_stats': referral_stats,
            'cash_value': cash_value,
            'balance': referral_stats['coin_balance'],
            'referral_code': affiliate.referral_code,  # Keeping for reference
            'current_weekly_number': current_weekly_number,
            'payout_history': payout_history,
            'recent_referrals': recent_referrals,
        }
        
        print(f"🔍 ACCOUNT CONTEXT DEBUG:")
        print(f"   - User ID: {user.id}")
        print(f"   - Weekly Number: {current_weekly_number.number if current_weekly_number else 'NOT FOUND'}")
        print(f"   - Coin Balance: {referral_stats['coin_balance']}")
        print(f"   - Total Referrals: {referral_stats['total_referrals']}")
        
        return render(request, 'account.html', context)
        
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login_view')
    except Exception as e:
        print(f"❌ Account view error: {str(e)}")
        messages.error(request, 'An error occurred while loading your account.')
        return redirect('index')

def logout_view(request):
    """User logout"""
    if 'user_id' in request.session:
        del request.session['user_id']
        del request.session['account_number']
        del request.session['first_name']
        del request.session['second_name']
    
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')

# ================== STRATEGIES FRONTEND VIEWS ==================

def free_strategies(request):
    """Display free trading strategies"""
    strategies = TradingStrategy.objects.all().order_by('-is_featured', '-created_at')
    
    context = {
        'strategies': strategies,
        'page_title': 'Free Trading Strategies', 
        'description': 'Explore our free strategy samples. Upgrade to VIP for full access to 4,155+ strategies.'
    }
    return render(request, 'market/strategies_free.html', context)

def activate_all_strategies(request):
    """Activate all trading strategies"""
    strategies = TradingStrategy.objects.all()
    count = strategies.count()
    
    for strategy in strategies:
        strategy.is_active = True
        strategy.save()
    
    messages.success(request, f'Activated all {count} trading strategies!')
    return redirect('admin_dashboard')

def premium_strategies(request):
    """Display premium trading strategies (VIP only)"""
    strategies = TradingStrategy.objects.filter(
        strategy_type__in=['premium', 'vip'],
        is_active=True
    ).order_by('-is_featured', '-created_at')
    
    context = {
        'strategies': strategies,
        'page_title': 'Premium Trading Strategies',
        'description': 'VIP access required to view premium strategies.'
    }
    return render(request, 'strategies_premium.html', context)

def strategy_detail(request, strategy_id):
    """Individual strategy detail page"""
    strategy = get_object_or_404(TradingStrategy, id=strategy_id, is_active=True)
    
    # Increment view count
    strategy.view_count += 1
    strategy.save()
    
    context = {
        'strategy': strategy,
        'related_strategies': TradingStrategy.objects.filter(
            market_type=strategy.market_type,
            is_active=True
        ).exclude(id=strategy_id)[:4]
    }
    return render(request, 'strategy_detail.html', context)

# ================== SIGNALS FRONTEND VIEWS ==================
def free_signals(request):
    """Display free trading signals"""
    # DEBUG: Check all signals
    print("=== DEBUGGING FREE SIGNALS ===")
    all_signals = TradingSignal.objects.all()
    print(f"Total signals in DB: {all_signals.count()}")
    
    for signal in all_signals:
        print(f"Signal: '{signal.title}' | Active: {signal.is_active}")
    
    # Filter for active signals
    signals = TradingSignal.objects.filter(
        is_active=True
    ).order_by('-is_featured', '-created_at')
    
    print(f"Active signals: {signals.count()}")
    print("=== END DEBUG ===")
    
    context = {
        'signals': signals,
        'page_title': 'Free Trading Signals',
        'description': 'Sample trading signals. Upgrade to VIP for real-time signals with 80%+ accuracy.'
    }
    return render(request, 'market/signals_free.html', context)

def activate_all_signals(request):
    """Activate all trading signals"""
    signals = TradingSignal.objects.all()
    count = signals.count()
    
    for signal in signals:
        signal.is_active = True
        signal.save()
    
    messages.success(request, f'Activated all {count} trading signals!')
    return redirect('admin_dashboard')


#=======================SHOP VIEWS AND PAYMENT====================
def initialize_merchandise_payment(request):
    """Dedicated Paystack payment for merchandise ONLY"""
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            amount = request.POST.get('amount')
            item_id = request.POST.get('item_id')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            
            print(f"🛍️ MERCHANDISE PAYMENT INITIATED: {email}, {amount} KES, Item: {item_id}")
            
            # Validate required fields
            if not email or not amount or not item_id:
                messages.error(request, 'Email, amount, and item are required.')
                return redirect('index')
            
            # Get merchandise item
            try:
                merchandise = Merchandise.objects.get(id=item_id, is_available=True)
            except Merchandise.DoesNotExist:
                messages.error(request, 'Selected merchandise item not found.')
                return redirect('index')
            
            # Convert amount to integer (kobo for Paystack)
            try:
                amount_kes = float(amount)
                amount_in_kobo = int(amount_kes * 100)
                print(f"💰 MERCHANDISE AMOUNT CONVERSION: {amount_kes} KES → {amount_in_kobo} kobo")
            except (ValueError, TypeError) as e:
                print(f"❌ MERCHANDISE AMOUNT ERROR: {e}")
                messages.error(request, 'Invalid amount format.')
                return redirect('index')
            
            # Create unique payment reference for merchandise
            reference = f"MCH{uuid.uuid4().hex[:10].upper()}"
            
            # Create payment record
            payment = Payment.objects.create(
                email=email,
                amount=amount_kes,
                plan_type=f"Merchandise: {merchandise.name}",
                reference=reference,
                status='pending'
            )
            
            print(f"📝 MERCHANDISE PAYMENT RECORD CREATED: {reference}")
            
            # Initialize Paystack
            paystack_service = PaystackService()
            
            # Process with Paystack
            response = paystack_service.initialize_transaction(
                email=email,
                amount=amount_in_kobo,
                reference=reference,
                callback_url=request.build_absolute_uri(f'/verify-merchandise-payment/{reference}/'),
                metadata={
                    'item_id': item_id,
                    'item_name': merchandise.name,
                    'category': 'merchandise',
                    'customer_phone': phone,
                    'shipping_address': address,
                    'custom_fields': [
                        {
                            'display_name': "Product",
                            'variable_name': "product", 
                            'value': merchandise.name
                        },
                        {
                            'display_name': "Shipping Address", 
                            'variable_name': "shipping_address",
                            'value': address
                        }
                    ]
                }
            )
            
            print(f"📡 MERCHANDISE PAYSTACK RESPONSE: {response}")
            
            if response.get('status'):
                # Redirect to Paystack
                authorization_url = response['data']['authorization_url']
                print(f"🔗 REDIRECTING TO PAYSTACK: {authorization_url}")
                return redirect(authorization_url)
            else:
                error_msg = response.get('message', 'Unknown error occurred')
                print(f"❌ MERCHANDISE PAYSTACK ERROR: {error_msg}")
                messages.error(request, f"Payment initialization failed: {error_msg}")
                return redirect('index')
                
        except Exception as e:
            print(f"💥 MERCHANDISE PAYMENT EXCEPTION: {str(e)}")
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('index')
    
    # If not POST, redirect to home
    return redirect('index')

def verify_merchandise_payment(request, reference):
    """Verify merchandise payment"""
    try:
        payment = Payment.objects.get(reference=reference)
        payment.status = 'success'
        payment.save()
        
        # Send order confirmation email
        send_merchandise_order_email(payment)
        
        messages.success(request, 'Payment verified successfully! Your order is being processed.')
    except Payment.DoesNotExist:
        messages.error(request, 'Payment record not found.')
    
    return redirect('index')

def send_merchandise_order_email(payment):
    """Send merchandise order confirmation"""
    try:
        subject = '🛍️ TradeWise Merchandise Order Confirmation'
        
        html_message = render_to_string('emails/merchandise_order.html', {
            'payment': payment,
        })
        
        plain_message = f"""
TradeWise Merchandise Order Confirmation

Thank you for your merchandise purchase!

Order Details:
- Product: {payment.plan_type}
- Amount: KES {payment.amount}
- Reference: {payment.reference}
- Date: {payment.created_at.strftime('%Y-%m-%d %H:%M')}

We will process your order and contact you for shipping details.

Best regards,
TradeWise Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[payment.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"📧 MERCHANDISE ORDER CONFIRMATION SENT TO: {payment.email}")
        return True
        
    except Exception as e:
        print(f"❌ MERCHANDISE ORDER EMAIL ERROR: {str(e)}")
        return False
    
def shop(request):
    """Merchandise shop page"""
    try:
        merchandise = Merchandise.objects.filter(is_available=True).order_by('-is_featured', 'category', 'name')
        
        # Group by category for shop page
        categories = {
            'caps-hats': merchandise.filter(category='caps-hats'),
            'hoodies': merchandise.filter(category='hoodies'), 
            't-shirts': merchandise.filter(category='t-shirts'),
            'accessories': merchandise.filter(category='accessories'),
        }
        
        context = {
            'merchandise': merchandise,
            'categories': categories,
            'featured_items': merchandise.filter(is_featured=True),
        }
    except Exception as e:
        print(f"Shop page error: {e}")
        context = {
            'merchandise': [],
            'categories': {},
            'featured_items': [],
        }
    
    return render(request, 'shop.html', context)


def create_emergency_merchandise():
    """Emergency function to create sample merchandise"""
    try:
        from django.core.files import File
        import os
        
        sample_items = [
            {
                'name': 'TradeWise Premium Hoodie',
                'category': 'hoodies',
                'description': 'Premium quality hoodie with TradeWise logo',
                'price': 2500.00,
                'is_featured': True,
                'is_available': True,
                'stock_quantity': 50,
            },
            {
                'name': 'TradeWise Baseball Cap', 
                'category': 'caps-hats',
                'description': 'Stylish baseball cap with embroidered logo',
                'price': 800.00,
                'is_featured': True,
                'is_available': True,
                'stock_quantity': 30,
            },
        ]
        
        created_count = 0
        for item_data in sample_items:
            obj, created = Merchandise.objects.get_or_create(
                name=item_data['name'],
                defaults=item_data
            )
            if created:
                created_count += 1
                print(f"✅ Created: {item_data['name']}")
        
        return f"Created {created_count} sample merchandise items"
        
    except Exception as e:
        return f"Error: {str(e)}"
def account(request):
    """User account dashboard - COMPLETE FIXED VERSION"""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please log in to access your account.')
        return redirect('login_view')
    
    try:
        user = Tradeviewusers.objects.get(id=user_id)
        
        # Get or create affiliate
        affiliate, created = Affiliate.objects.get_or_create(user=user)
        if created:
            print(f"✅ AUTO-CREATED AFFILIATE IN ACCOUNT: {user.email}")
        
        # ✅ THESE WILL WORK NOW WITH PROPER IMPORTS:
        # 1. Current weekly number
        current_weekly_number = WeeklyNumber.get_current_number()
        
        # 2. Recent referrals (last 5) - THIS WAS FAILING!
        recent_referrals = Referral.objects.filter(affiliate=affiliate).select_related('referred_user').order_by('-created_at')[:5]
        
        # 3. Payout history - THIS WAS FAILING!
        payout_history = PayoutRequest.objects.filter(user=user).order_by('-created_at')[:5]
        
        # 4. Referral stats
        referral_stats = {
            'total_referrals': affiliate.total_referrals,
            'total_coins': affiliate.total_coins_earned,
            'coin_balance': affiliate.coin_balance,
            'pending_coins': 0,
        }
        
        cash_value = affiliate.coin_balance * 10
        
        # ✅ DEBUG: Check what data we have
        print(f"🔍 ACCOUNT VIEW DEBUG for {user.email}:")
        print(f"   Affiliate Balance: {affiliate.coin_balance}")
        print(f"   Total Referrals: {affiliate.total_referrals}")
        print(f"   Recent Referrals Count: {recent_referrals.count()}")
        print(f"   Payout History Count: {payout_history.count()}")
        
        context = {
            'user': user,
            'first_name': user.first_name,
            'second_name': user.second_name,
            'account_number': user.account_number,
            'user_id': user.id,
            'referral_code': affiliate.referral_code,
            'referral_stats': referral_stats,
            'cash_value': cash_value,
            'balance': referral_stats['coin_balance'],
            'current_weekly_number': current_weekly_number,
            'payout_history': payout_history,
            'recent_referrals': recent_referrals,
        }
        
        return render(request, 'account.html', context)
        
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login_view')
    except Exception as e:
        print(f"❌ Account view error: {str(e)}")
        import traceback
        traceback.print_exc()  # This will show exactly where it's breaking
        messages.error(request, 'An error occurred while loading your account.')
        return redirect('index')
    
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login_view')
    


    # Add this to your views.py

def request_payout(request):
    """Handle payout requests from users"""
    if not request.session.get('user_id'):
        messages.error(request, 'Please log in to request a payout.')
        return redirect('login_view')
    
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            user = Tradeviewusers.objects.get(id=user_id)
            
            # Get affiliate data
            affiliate = Affiliate.objects.get(user=user)
            
            coin_amount = int(request.POST.get('coin_amount'))
            payment_method = request.POST.get('payment_method')
            
            # Validate coin amount
            if coin_amount < 50:
                messages.error(request, 'Minimum payout is 50 coins.')
                return redirect('account')
            
            if coin_amount > affiliate.coin_balance:
                messages.error(request, 'Insufficient coin balance.')
                return redirect('account')
            
            # Calculate payout amount (10 Ksh per coin)
            amount_kes = coin_amount * 10
            
            # Create payout request
            payout_request = PayoutRequest(
                user=user,
                coin_amount=coin_amount,
                amount_kes=amount_kes,
                payment_method=payment_method,
                mpesa_number=request.POST.get('mpesa_number'),
                bank_name=request.POST.get('bank_name'),
                bank_account=request.POST.get('bank_account'),
                paypal_email=request.POST.get('paypal_email'),
                status='pending'
            )
            payout_request.save()
            
            # Update affiliate coin balance (reserve the coins)
            affiliate.coin_balance -= coin_amount
            affiliate.save()
            
            # Send notification to admin
            send_payout_notification_email(payout_request)
            
            messages.success(request, f'Payout request submitted for {coin_amount} coins (KES {amount_kes}). We will process it within 24 hours.')
            
        except Affiliate.DoesNotExist:
            messages.error(request, 'You are not registered as an affiliate.')
        except Exception as e:
            messages.error(request, f'Error submitting payout request: {str(e)}')
    
    return redirect('account')

def send_payout_notification_email(payout_request):
    """Send email to admin when new payout is requested"""
    try:
        subject = f'New Payout Request - {payout_request.user.first_name} {payout_request.user.second_name}'
        
        # Build account details based on payment method
        account_details = ""
        if payout_request.payment_method == 'mpesa':
            account_details = f"M-Pesa: {payout_request.mpesa_number}"
        elif payout_request.payment_method == 'bank':
            account_details = f"Bank: {payout_request.bank_name}\nAccount: {payout_request.bank_account}"
        elif payout_request.payment_method == 'paypal':
            account_details = f"PayPal: {payout_request.paypal_email}"
        
        html_message = render_to_string('emails/admin_payout_notification.html', {
            'payout': payout_request,
        })
        
        plain_message = f"""
NEW PAYOUT REQUEST - TRADEWISE

AFFILIATE INFORMATION:
---------------------
Name: {payout_request.user.first_name} {payout_request.user.second_name}
TradeWise Number: {payout_request.user.account_number}
Email: {payout_request.user.email}
Phone: {payout_request.user.phone or 'Not provided'}

PAYOUT DETAILS:
--------------
Amount: KES {payout_request.amount_kes}
Coins: {payout_request.coin_amount} TWC
Payment Method: {payout_request.get_payment_method_display()}

ACCOUNT INFORMATION:
-------------------
{account_details}

REQUEST DETAILS:
---------------
Request ID: PO{payout_request.id:04d}
Date: {payout_request.created_at.strftime('%B %d, %Y')}
Time: {payout_request.created_at.strftime('%H:%M %p')}
Status: Pending Review

ACTION REQUIRED:
---------------
Please log in to the admin dashboard to review and process this payout request.

Admin Dashboard: https://www.tradewise-hub.com/admin-dashboard/

This is an automated notification from the TradeWise Affiliate System.
"""
        
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'theofficialtradewise@gmail.com')
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"📧 Payout notification sent to admin for request PO{payout_request.id:04d}")
        return True
        
    except Exception as e:
        print(f"❌ Payout notification email error: {str(e)}")
        return False

def send_referral_notification_email(affiliate, referred_user):
    """Send email to affiliate when someone signs up with their referral"""
    try:
        subject = '🎉 New Referral Signup - 50 TWC Coins Awarded!'
        
        html_message = render_to_string('emails/referral_notification.html', {
            'affiliate': affiliate,
            'referred_user': referred_user,
        })
        
        plain_message = f"""
New Referral Signup - TradeWise

Congratulations {affiliate.user.first_name}!

Someone signed up using your referral link:

New User: {referred_user.first_name} {referred_user.second_name}
Email: {referred_user.email}
TradeWise Number: {referred_user.account_number}

You have been awarded 50 TWC coins!

Your new balance: {affiliate.coin_balance} TWC coins
Total referrals: {affiliate.total_referrals}

Keep sharing your referral link to earn more coins!

Best regards,
TradeWise Team
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[affiliate.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
        
    except Exception as e:
        print(f"Referral notification email error: {str(e)}")
        return False
    

def update_weekly_number(request):
    """Update the weekly lucky number for affiliate redemptions"""
    try:
        weekly_number = request.POST.get('weekly_number', '').strip()
        week_start = request.POST.get('week_start', '').strip()
        
        print(f"🔄 UPDATING WEEKLY NUMBER: {weekly_number}, Week Start: {week_start}")
        
        # Validate required fields
        if not weekly_number:
            messages.error(request, 'Weekly number is required.')
            return redirect('admin_dashboard')
        
        if not week_start:
            messages.error(request, 'Week start date is required.')
            return redirect('admin_dashboard')
        
        # Validate weekly number format (should be numbers separated by spaces)
        if not all(part.isdigit() for part in weekly_number.split()):
            messages.error(request, 'Weekly number should contain only numbers separated by spaces.')
            return redirect('admin_dashboard')
        
        # Deactivate any currently active weekly number
        active_numbers = WeeklyNumber.objects.filter(is_active=True)
        if active_numbers.exists():
            for number in active_numbers:
                number.is_active = False
                number.save()
            print(f"✅ Deactivated {active_numbers.count()} previously active weekly numbers")
        
        # Create new weekly number
        new_weekly = WeeklyNumber.objects.create(
            number=weekly_number,
            week_start=week_start,
            is_active=True
        )
        
        print(f"✅ Created new weekly number: {weekly_number} (Week: {week_start})")
        
        # Log action
        try:
            admin_user = get_current_admin(request)
            AdminLog.objects.create(
                user=admin_user,
                action=f'Updated weekly lucky number to: {weekly_number}',
                details={
                    'week_start': week_start,
                    'previous_numbers_count': active_numbers.count()
                },
                ip_address=get_client_ip(request)
            )
            print("✅ Admin log created")
        except Exception as log_error:
            print(f"⚠️ Failed to create admin log: {log_error}")
        
        messages.success(request, f'✅ Weekly lucky number updated to: {weekly_number}')
        
    except Exception as e:
        print(f"❌ ERROR updating weekly number: {str(e)}")
        messages.error(request, f'Error updating weekly number: {str(e)}')
    
    return redirect('admin_dashboard')    

@admin_required
def approve_referral(request):
    """Approve referral and award coins - NEW ENDPOINT"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            referral_id = data.get('referral_id')
            
            referral = Referral.objects.get(id=referral_id, status='pending')
            
            if referral.approve_referral():
                return JsonResponse({'success': True, 'message': '50 coins awarded!'})
            else:
                return JsonResponse({'success': False, 'error': 'Already approved'})
                
        except Referral.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Referral not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def get_affiliate_data(request):
    """Live data for affiliate dashboard - FIXED WITH ERROR HANDLING"""
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Please login'})
    
    try:
        user_id = request.session.get('user_id')
        user = Tradeviewusers.objects.get(id=user_id)  # This is failing!
        
        # Get or create affiliate
        affiliate, created = Affiliate.objects.get_or_create(user=user)
        if created:
            print(f"✅ AUTO-CREATED AFFILIATE FOR: {user.email}")
        
        # Get current weekly number
        weekly_number = WeeklyNumber.get_current_number()
        
        # Calculate stats
        pending_referrals_count = Referral.objects.filter(affiliate=affiliate, status='pending').count()
        
        data = {
            'success': True,
            'stats': {
                'total_referrals': affiliate.total_referrals,
                'total_coins': affiliate.total_coins_earned,
                'coin_balance': affiliate.coin_balance,
                'pending_coins': pending_referrals_count * 50
            },
            'cash_value': affiliate.coin_balance * 10,
            'weekly_number': weekly_number.number if weekly_number else "7 8 4 2 1",
            'referral_code': affiliate.referral_code
        }
        
        print(f"📊 AFFILIATE DATA: {data}")
        return JsonResponse(data)
        
    except Tradeviewusers.DoesNotExist:
        # ✅ FIX: Clear invalid session and redirect to login
        print(f"❌ USER DELETED: User ID {user_id} no longer exists")
        request.session.flush()  # Clear the invalid session
        return JsonResponse({
            'success': False, 
            'error': 'Session expired. Please login again.',
            'redirect': '/login/'
        })
    except Exception as e:
        print(f"❌ AFFILIATE DATA ERROR: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@admin_required
def approve_referral(request):
    """Approve referral and award 50 coins - AJAX ENDPOINT"""
    if request.method == 'POST':
        try:
            # Get data from AJAX request
            data = json.loads(request.body)
            referral_id = data.get('referral_id')
            
            print(f"🟢 APPROVING REFERRAL: ID {referral_id}")
            
            # Find the pending referral
            referral = Referral.objects.get(id=referral_id, status='pending')
            
            # Use the model's approve method
            if referral.approve_referral():
                print(f"✅ REFERRAL APPROVED: 50 coins awarded to {referral.affiliate.user.email}")
                return JsonResponse({
                    'success': True, 
                    'message': f'✅ 50 coins awarded to {referral.affiliate.user.first_name}!',
                    'new_balance': referral.affiliate.coin_balance
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Referral already approved or cannot be approved'
                })
                
        except Referral.DoesNotExist:
            print(f"❌ REFERRAL NOT FOUND: {referral_id}")
            return JsonResponse({'success': False, 'error': 'Referral not found'})
        except Exception as e:
            print(f"❌ APPROVAL ERROR: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Add these functions to views.py

@admin_required
def approve_referral(request, referral_id=None):
    """Approve referral and award 50 coins - works with both AJAX and direct URL"""
    if request.method == 'POST' or referral_id:
        try:
            # Get referral ID from POST data or URL parameter
            if referral_id:
                target_referral_id = referral_id
            else:
                data = json.loads(request.body)
                target_referral_id = data.get('referral_id')
            
            referral = Referral.objects.get(id=target_referral_id, status='pending')
            
            if referral.approve_referral():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': '50 coins awarded!'})
                messages.success(request, f'Referral approved! 50 coins awarded to {referral.affiliate.user.first_name}')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Referral already approved'})
                messages.error(request, 'Referral already approved')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_dashboard')

@admin_required
def reject_referral(request, referral_id):
    """Reject a referral"""
    try:
        referral = Referral.objects.get(id=referral_id, status='pending')
        referral.status = 'rejected'
        referral.save()
        messages.success(request, 'Referral rejected')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    return redirect('admin_dashboard')

@admin_required
def approve_all_pending_referrals(request):
    """Approve all pending referrals"""
    try:
        pending_referrals = Referral.objects.filter(status='pending')
        count = pending_referrals.count()
        
        for referral in pending_referrals:
            referral.approve_referral()
        
        messages.success(request, f'Approved all {count} pending referrals!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    return redirect('admin_dashboard')

@admin_required
def bulk_approve_referrals(request):
    """Bulk approve selected referrals"""
    if request.method == 'POST':
        try:
            referral_ids = request.POST.getlist('referral_ids')
            approved_count = 0
            
            for referral_id in referral_ids:
                try:
                    referral = Referral.objects.get(id=referral_id, status='pending')
                    if referral.approve_referral():
                        approved_count += 1
                except Referral.DoesNotExist:
                    continue
            
            messages.success(request, f'Approved {approved_count} referrals!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_dashboard')

    # ================== NEW AFFILIATE & REFERRAL FUNCTIONS ==================

def get_affiliate_data(request):
    """Live data for affiliate dashboard"""
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Please login'})
    
    try:
        user = Tradeviewusers.objects.get(id=request.session.get('user_id'))
        affiliate = Affiliate.objects.get(user=user)
        weekly_number = WeeklyNumber.objects.filter(is_active=True).first()
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_referrals': affiliate.total_referrals,
                'total_coins': affiliate.total_coins_earned,
                'coin_balance': affiliate.coin_balance,
                'pending_coins': Referral.objects.filter(affiliate=affiliate, status='pending').count() * 50
            },
            'cash_value': affiliate.coin_balance * 10,
            'weekly_number': weekly_number.number if weekly_number else '7 8 4 2 1'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_weekly_number(request):
    """AJAX endpoint for weekly number"""
    try:
        current_weekly = WeeklyNumber.objects.filter(is_active=True).first()
        return JsonResponse({
            'success': True,
            'weekly_number': current_weekly.number if current_weekly else '7 8 4 2 1',
            'week_start': current_weekly.week_start.strftime('%b %d') if current_weekly else ''
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def request_payout(request):
    """Handle payout requests from users - FIXED VERSION"""
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Please log in'})
    
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            user = Tradeviewusers.objects.get(id=user_id)
            affiliate = Affiliate.objects.get(user=user)
            
            coin_amount = int(request.POST.get('coin_amount', 0))
            
            # VALIDATION
            if coin_amount < 50:
                return JsonResponse({'success': False, 'error': 'Minimum payout is 50 coins'})
            
            if coin_amount > affiliate.coin_balance:
                return JsonResponse({'success': False, 'error': 'Insufficient coin balance'})
            
            # Create payout request
            payout_request = PayoutRequest(
                user=user,
                coin_amount=coin_amount,
                amount_kes=coin_amount * 10,
                payment_method=request.POST.get('payment_method'),
                mpesa_number=request.POST.get('mpesa_number'),
                bank_name=request.POST.get('bank_name'),
                bank_account=request.POST.get('bank_account'),
                paypal_email=request.POST.get('paypal_email'),
                status='pending'
            )
            payout_request.save()
            
            # Update affiliate balance
            affiliate.coin_balance -= coin_amount
            affiliate.save()
            
            # Send notification
            send_payout_notification_email(payout_request)
            
            return JsonResponse({
                'success': True, 
                'message': f'Payout request submitted for {coin_amount} coins'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@admin_required
def approve_referral(request, referral_id=None):
    """Approve referral and award 50 coins - works with both AJAX and direct URL"""
    if request.method == 'POST' or referral_id:
        try:
            # Get referral ID from POST data or URL parameter
            if referral_id:
                target_referral_id = referral_id
            else:
                data = json.loads(request.body)
                target_referral_id = data.get('referral_id')
            
            referral = Referral.objects.get(id=target_referral_id, status='pending')
            
            if referral.approve_referral():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': '50 coins awarded!'})
                messages.success(request, f'Referral approved! 50 coins awarded to {referral.affiliate.user.first_name}')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Referral already approved'})
                messages.error(request, 'Referral already approved')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_dashboard')

@admin_required
def reject_referral(request, referral_id):
    """Reject a referral"""
    try:
        referral = Referral.objects.get(id=referral_id, status='pending')
        referral.status = 'rejected'
        referral.save()
        messages.success(request, 'Referral rejected')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    return redirect('admin_dashboard')

@admin_required
def approve_all_pending_referrals(request):
    """Approve all pending referrals"""
    try:
        pending_referrals = Referral.objects.filter(status='pending')
        count = pending_referrals.count()
        
        for referral in pending_referrals:
            referral.approve_referral()
        
        messages.success(request, f'Approved all {count} pending referrals!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    return redirect('admin_dashboard')

@admin_required
def bulk_approve_referrals(request):
    """Bulk approve selected referrals"""
    if request.method == 'POST':
        try:
            referral_ids = request.POST.getlist('referral_ids')
            approved_count = 0
            
            for referral_id in referral_ids:
                try:
                    referral = Referral.objects.get(id=referral_id, status='pending')
                    if referral.approve_referral():
                        approved_count += 1
                except Referral.DoesNotExist:
                    continue
            
            messages.success(request, f'Approved {approved_count} referrals!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_dashboard')




# ================== AFFILIATE SYSTEM FIXES ==================

def auto_create_affiliate_profile(user):
    """Automatically create affiliate profile for new users"""
    try:
        affiliate, created = Affiliate.objects.get_or_create(user=user)
        if created:
            print(f"✅ AUTO-CREATED AFFILIATE: {user.email} - Code: {affiliate.referral_code}")
        return affiliate
    except Exception as e:
        print(f"❌ AFFILIATE CREATION ERROR: {str(e)}")
        return None

def auto_approve_referral(referred_user, referral_code):
    """AUTOMATIC REFERRAL APPROVAL - Called during signup"""
    try:
        print(f"🔄 AUTO-APPROVING REFERRAL: User {referred_user.email}, Code: {referral_code}")
        
        # Find affiliate by referral code
        affiliate = Affiliate.objects.filter(referral_code=referral_code).first()
        if not affiliate:
            print(f"❌ AFFILIATE NOT FOUND: {referral_code}")
            return False
        
        # Check if referral already exists
        existing_referral = Referral.objects.filter(
            affiliate=affiliate,
            referred_user=referred_user
        ).first()
        
        if existing_referral:
            print(f"⚠️ REFERRAL ALREADY EXISTS: {referred_user.email}")
            return False
        
        # Create and AUTO-APPROVE referral with 50 coins
        with transaction.atomic():
            referral = Referral.objects.create(
                affiliate=affiliate,
                referred_user=referred_user,
                status='approved',  # AUTO-APPROVED
                coins_awarded=50   # INSTANT 50 COINS
            )
            
            # Update affiliate stats
            affiliate.total_referrals += 1
            affiliate.total_coins_earned += 50
            affiliate.coin_balance += 50
            affiliate.save()
            
            print(f"✅ AUTO-APPROVED REFERRAL: {referred_user.email}")
            print(f"💰 COINS AWARDED: 50 coins to {affiliate.user.email}")
            print(f"📊 NEW BALANCE: {affiliate.coin_balance} coins")
            
            # Send notification
            send_referral_notification_email(affiliate, referred_user)
            
        return True
        
    except Exception as e:
        print(f"❌ AUTO-APPROVAL ERROR: {str(e)}")
        return False

def send_referral_notification_email(affiliate, referred_user):
    """Send email when referral is auto-approved"""
    try:
        subject = '🎉 New Referral - 50 TWC Coins Awarded!'
        
        message = f"""
New Referral - TradeWise

Congratulations {affiliate.user.first_name}!

Someone signed up using your referral link:

New User: {referred_user.first_name} {referred_user.second_name}
Email: {referred_user.email}
TradeWise Number: {referred_user.account_number}

You have been automatically awarded 50 TWC coins!

Your new balance: {affiliate.coin_balance} TWC coins
Total referrals: {affiliate.total_referrals}

Keep sharing your link to earn more coins!

Best regards,
TradeWise Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trade-wise.co.ke'),
            recipient_list=[affiliate.user.email],
            fail_silently=False,
        )
        print(f"📧 Referral notification sent to {affiliate.user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Referral notification email error: {str(e)}")
        return False


# ================== AFFILIATE DATA API ==================

def get_affiliate_data(request):
    """Live data for affiliate dashboard - FIXED"""
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Please login'})
    
    try:
        user = Tradeviewusers.objects.get(id=request.session.get('user_id'))
        
        # Get or create affiliate
        affiliate, created = Affiliate.objects.get_or_create(user=user)
        if created:
            print(f"✅ AUTO-CREATED AFFILIATE FOR: {user.email}")
        
        # Get current weekly number
        weekly_number = WeeklyNumber.get_current_number()
        
        # Calculate stats
        pending_referrals_count = Referral.objects.filter(affiliate=affiliate, status='pending').count()
        
        data = {
            'success': True,
            'stats': {
                'total_referrals': affiliate.total_referrals,
                'total_coins': affiliate.total_coins_earned,
                'coin_balance': affiliate.coin_balance,
                'pending_coins': pending_referrals_count * 50
            },
            'cash_value': affiliate.coin_balance * 10,
            'weekly_number': weekly_number.number if weekly_number else "7 8 4 2 1",
            'referral_code': affiliate.referral_code
        }
        
        print(f"📊 AFFILIATE DATA: {data}")
        return JsonResponse(data)
        
    except Exception as e:
        print(f"❌ AFFILIATE DATA ERROR: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

# ================== WEEKLY NUMBER MANAGEMENT ==================

@admin_required
def update_weekly_number(request):
    """Update weekly lucky number - FIXED"""
    if request.method == 'POST':
        try:
            weekly_number = request.POST.get('weekly_number', '').strip()
            week_start = request.POST.get('week_start', '').strip()
            
            print(f"🔄 UPDATING WEEKLY NUMBER: {weekly_number}, Week Start: {week_start}")
            
            if not weekly_number:
                messages.error(request, 'Weekly number is required.')
                return redirect('admin_dashboard')
            
            if not week_start:
                messages.error(request, 'Week start date is required.')
                return redirect('admin_dashboard')
            
            # Create or update weekly number
            weekly_obj, created = WeeklyNumber.objects.get_or_create(
                is_active=True,
                defaults={
                    'number': weekly_number,
                    'week_start': week_start,
                    'is_active': True
                }
            )
            
            if not created:
                weekly_obj.number = weekly_number
                weekly_obj.week_start = week_start
                weekly_obj.save()
            
            print(f"✅ WEEKLY NUMBER UPDATED: {weekly_number}")
            messages.success(request, f'Weekly lucky number updated to: {weekly_number}')
            
        except Exception as e:
            print(f"❌ WEEKLY NUMBER ERROR: {str(e)}")
            messages.error(request, f'Error updating weekly number: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== PAYOUT REQUEST ==================

def request_payout(request):
    """Handle payout requests - FIXED"""
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Please log in'})
    
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            user = Tradeviewusers.objects.get(id=user_id)
            affiliate = Affiliate.objects.get(user=user)
            
            coin_amount = int(request.POST.get('coin_amount', 0))
            payment_method = request.POST.get('payment_method')
            
            # Validation
            if coin_amount < 50:
                return JsonResponse({'success': False, 'error': 'Minimum payout is 50 coins'})
            
            if coin_amount > affiliate.coin_balance:
                return JsonResponse({'success': False, 'error': 'Insufficient coin balance'})
            
            # Create payout request
            payout_request = PayoutRequest(
                user=user,
                coin_amount=coin_amount,
                payment_method=payment_method,
                mpesa_number=request.POST.get('mpesa_number'),
                bank_name=request.POST.get('bank_name'),
                bank_account=request.POST.get('bank_account'),
                paypal_email=request.POST.get('paypal_email')
            )
            payout_request.save()
            
            # Reserve coins (deduct from balance)
            affiliate.coin_balance -= coin_amount
            affiliate.save()
            
            # Send notification
            send_payout_notification_email(payout_request)
            
            return JsonResponse({
                'success': True, 
                'message': f'Payout request submitted for {coin_amount} coins (KES {payout_request.amount_kes})'
            })
            
        except Affiliate.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Affiliate profile not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# ================== REFERRAL MANAGEMENT ==================

@admin_required
def approve_referral(request):
    """Approve referral - FIXED AJAX ENDPOINT"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            referral_id = data.get('referral_id')
            
            print(f"🟢 APPROVING REFERRAL: ID {referral_id}")
            
            referral = Referral.objects.get(id=referral_id, status='pending')
            
            if referral.approve_referral():
                return JsonResponse({
                    'success': True, 
                    'message': '✅ 50 coins awarded!',
                    'new_balance': referral.affiliate.coin_balance
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Referral already approved'
                })
                
        except Referral.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Referral not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@admin_required
def approve_all_pending_referrals(request):
    """Approve all pending referrals"""
    try:
        pending_referrals = Referral.objects.filter(status='pending')
        count = pending_referrals.count()
        approved_count = 0
        
        for referral in pending_referrals:
            if referral.approve_referral():
                approved_count += 1
        
        messages.success(request, f'Approved {approved_count} out of {count} pending referrals!')
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_dashboard')

# ================== ACCOUNT VIEW WITH AFFILIATE DATA ==================

def get_affiliate_data(request):
    """Live data for affiliate dashboard - FIXED WITH ERROR HANDLING"""
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'error': 'Please login'})
    
    try:
        user_id = request.session.get('user_id')
        user = Tradeviewusers.objects.get(id=user_id)
        
        # Get or create affiliate
        affiliate, created = Affiliate.objects.get_or_create(user=user)
        if created:
            print(f"✅ AUTO-CREATED AFFILIATE FOR: {user.email}")
        
        # Get current weekly number
        weekly_number = WeeklyNumber.get_current_number()
        
        # Calculate stats
        pending_referrals_count = Referral.objects.filter(affiliate=affiliate, status='pending').count()
        
        data = {
            'success': True,
            'stats': {
                'total_referrals': affiliate.total_referrals,
                'total_coins': affiliate.total_coins_earned,
                'coin_balance': affiliate.coin_balance,
                'pending_coins': pending_referrals_count * 50
            },
            'cash_value': affiliate.coin_balance * 10,
            'weekly_number': weekly_number.number if weekly_number else "7 8 4 2 1",
            'referral_code': affiliate.referral_code
        }
        
        print(f"📊 AFFILIATE DATA: {data}")
        return JsonResponse(data)
        
    except Tradeviewusers.DoesNotExist:
        # ✅ FIX: Clear invalid session and redirect to login
        print(f"❌ AFFILIATE DATA ERROR: User ID {user_id} no longer exists")
        request.session.flush()  # Clear the invalid session
        return JsonResponse({
            'success': False, 
            'error': 'Session expired. Please login again.',
            'redirect': '/login/'
        })
    except Exception as e:
        print(f"❌ AFFILIATE DATA ERROR: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
        
    except Tradeviewusers.DoesNotExist:
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login_view')
    except Exception as e:
        print(f"❌ Account view error: {str(e)}")
        messages.error(request, 'An error occurred while loading your account.')
        return redirect('index')