from django.urls import path
from django.views.generic import RedirectView
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ================== WEBSITE AUTHENTICATION URLS ==================
    path('', views.index, name='index'),
    path('loginpage/', views.login_page, name='login_page'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account, name='account'),
    
    # ================== ENHANCED AUTHENTICATION URLS ==================
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # ================== ADMIN REDIRECT ==================
    path('admin/', RedirectView.as_view(url='/admin/login/', permanent=False)),
    
    # ================== ADMIN DASHBOARD URLS ==================
    path('admin/login/', views.enhanced_admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    
    # Main Admin Dashboard
    path('admin/dashboard/', views.admin_dashboard_main, name='admin_dashboard'),
    
    # ================== LIVE DASHBOARD AJAX ENDPOINTS ==================
    
    # Live Revenue Data for Charts - USING FUNCTION-BASED VIEWS
    path('admin/ajax/revenue-data/', views.ajax_revenue_data, name='revenue_data'),
    
    # Recent Activity Feed - USING FUNCTION-BASED VIEWS
    path('admin/ajax/activity-data/', views.ajax_activity_data, name='activity_data'),
    
    # Quick Stats Updates - USING FUNCTION-BASED VIEWS
    path('admin/ajax/quick-stats/', views.ajax_quick_stats, name='quick_stats'),
    
    # Users Management Data - USING FUNCTION-BASED VIEWS
    path('admin/ajax/users-data/', views.ajax_users_data, name='users_data'),
    
    # Requests Management Data - USING FUNCTION-BASED VIEWS
    path('admin/ajax/requests-data/', views.ajax_requests_data, name='requests_data'),
    
    # User Details AJAX
    path('admin/ajax/user-details/<int:user_id>/', views.user_details_ajax, name='user_details_ajax'),

    # API Endpoints for Admin Dashboard
    path('admin/api/stats/', views.admin_get_dashboard_stats, name='admin_api_stats'),

    # ================== WEBSITE PAGE URLS ==================
    path('coaching/', views.coaching, name='coaching'),
    path('market/', views.market_hub, name='market_hub'),
    path('trade/', views.trade, name='trade'),
    path('contact/', views.contact, name='contact'),
    path('merchandise/', views.merchandise, name='merchandise'),
    path('services/', views.services_page, name='services_page'),
    path('classes/', views.classes_view, name='classes'),
    path('learning-hub/', views.learning_hub, name='learning_hub'),

    # ================== BLOG URLS ==================
    path('blog/', views.blog_page, name='blog_page'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),

    # ================== MARKET HUB AJAX URLS ==================
    path('ajax/market/strategies/', views.ajax_market_strategies, name='ajax_market_strategies'),
    path('ajax/market/signals/', views.ajax_market_signals, name='ajax_market_signals'), 
    path('ajax/market/software/', views.ajax_market_software, name='ajax_market_software'),
    path('ajax/software-details/<int:id>/', views.ajax_software_details, name='ajax_software_details'),
    path('ajax/track-download/<int:id>/', views.track_download, name='track_download'),
    
    # ================== USER DASHBOARD URLS ==================
    path('dashboard/', views.account, name='dashboard'),
    
    # ================== PAYMENT & E-COMMERCE URLS ==================
    path('payment/', views.payment, name='payment'),
    path('merchandise/payment/<int:id>/', views.merchandise_payment, name='merchandise_payment'),
    path('merchandise/<str:category>/', views.merchandise_by_category, name='merchandise_by_category'),
    
    # ================== PAYSTACK PAYMENT URLS ==================
    path('pricing/', views.pricing_plans, name='pricing_plans'),
    path('payment/initialize/<int:plan_id>/', views.initialize_plan_payment, name='initialize_payment'),
    path('payment/verify/<str:reference>/', views.verify_payment, name='verify_payment'),
    path('payment/webhook/', views.paystack_webhook, name='paystack_webhook'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    
    # ================== MERCHANDISE PAYMENT URLS ==================
    path('merchandise/process-payment/', views.process_merchandise_payment, name='process_merchandise_payment'),
    path('merchandise/payment/verify/<str:reference>/', views.verify_merchandise_payment, name='verify_merchandise_payment'),
    
    # ================== MPESA PAYMENT URLS ==================
    path('mpesa_checkout/', views.mpesa_checkout, name='mpesa_checkout'),
    path('mpesa_checkouts/', views.mpesa_checkouts, name='mpesa_checkouts'),
    path('loading/', views.loading, name='loading'),
    
    # ================== CONTENT & ANALYSIS URLS ==================
    path('analysis/<int:pk>/', views.analysis_detail, name='analysis_detail'),
    path('shop/<str:category>/', views.merchandise_by_category, name='merchandise_by_category'),
    
    # ================== FORM SUBMISSION URLS ==================
    path('submit_consultation/', views.submit_consultation, name='submit_consultation'),
    path('submit-service-request/', views.submit_service_request, name='submit_service_request'),
    path('submit_service_request/', views.submit_service_request, name='submit_service_request'),
    path('submit-class-request/', views.submit_class_request, name='submit_class_request'),
    
    # ================== SOFTWARE MANAGEMENT URLS ==================
    path('ajax/software-details/<int:id>/', views.ajax_software_details, name='ajax_software_details'),
    path('admin/ajax/software-details/<int:id>/', views.ajax_software_details, name='admin_software_details'),
    path('ajax/track-download/<int:id>/', views.track_download, name='track_download'),
    path('admin/track-download/<int:id>/', views.track_download, name='admin_track_download'),

    # ================== REVIEWS SYSTEM URLS ==================
    path('submit-review/', views.submit_review, name='submit_review'),
    path('api/reviews/', views.get_reviews_for_frontend, name='get_reviews'),
    path('admin/ajax/review-details/<int:review_id>/', views.review_details_ajax, name='review_details_ajax'),
    
    # ================== AFFILIATE SYSTEM URLS ==================
    # User Affiliate URLs
    path('affiliate/', views.affiliate_dashboard, name='affiliate_dashboard'),
    path('affiliate/request-payout/', views.request_payout, name='request_payout'),
    path('affiliate/share/<str:platform>/', views.share_referral, name='share_referral'),
    
    # Admin Affiliate Management URLs
    path('admin/ajax/payout-details/<int:payout_id>/', views.payout_details_ajax, name='payout_details_ajax'),
    path('admin/ajax/affiliate-details/<int:user_id>/', views.affiliate_details_ajax, name='affiliate_details_ajax'),

    # ================== NEWSLETTER SUBSCRIPTION URLS ==================
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('unsubscribe-newsletter/<str:email>/', views.unsubscribe_newsletter, name='unsubscribe_newsletter'),

    # ================== DEBUG & UTILITY URLS ==================
    path('admin/debug/reviews/', views.debug_reviews, name='debug_reviews'),
    
    # ================== TRADEWISE CARD & COIN URLS ==================
    path('ajax/card-data/', views.ajax_card_data, name='ajax_card_data'),
    
    # ================== ADDITIONAL AJAX ENDPOINTS ==================
    path('ajax/merchandise-data/', views.ajax_merchandise_data, name='ajax_merchandise_data'),
    path('ajax/general-stats/', views.ajax_general_stats, name='ajax_general_stats'),
    path('ajax/live-updates/', views.ajax_live_updates, name='ajax_live_updates'),
    path('ajax/dashboard-widgets/', views.ajax_dashboard_widgets, name='ajax_dashboard_widgets'),
    
    # ================== BLOG AJAX ENDPOINTS ==================
    path('ajax/blog-posts/', views.get_blog_posts_ajax, name='get_blog_posts_ajax'),
    path('admin/ajax/blog-post-details/<int:post_id>/', views.blog_post_details_ajax, name='blog_post_details_ajax'),

    # ================== ADDITIONAL URLS FOR COMPATIBILITY ==================
    path('login_view/', views.login_view, name='login_view'),
    path('logout_view/', views.logout_view, name='logout_view'),
    path('market_hub/', views.market_hub, name='market_hub'),
    path('classes_view/', views.classes_view, name='classes_view'),
    # Blog URLs
    path('blog/', views.blog_home, name='blog_home'),
    path('blog/post/<int:id>/', views.blog_detail, name='blog_detail'),
    path('blog/ajax/posts/', views.blog_posts_ajax, name='blog_posts_ajax'),
    path('blog/create/', views.create_blog_post, name='create_blog_post'),
    path('blog/debug/', views.blog_debug, name='blog_debug'),


    # Merchandise URLs
path('merchandise/', views.merchandise_home, name='merchandise_home'),
path('merchandise/category/<str:category>/', views.merchandise_category, name='merchandise_category'),
path('ajax/merchandise-data/', views.ajax_merchandise_data, name='ajax_merchandise_data'),
path('merchandise/payment/process/', views.process_merchandise_payment, name='process_merchandise_payment'),



  # Public review routes
    path('api/reviews/', views.reviews_api, name='reviews_api'),
    path('submit-review/', views.submit_review, name='submit_review'),
    
    # Admin review management routes
    path('admin/reviews/', views.admin_reviews_management, name='admin_reviews_management'),
    path('admin/reviews/add/', views.add_review_admin, name='add_review_admin'),
    path('admin/reviews/approve/<int:review_id>/', views.approve_review, name='approve_review'),
    path('admin/reviews/feature/<int:review_id>/', views.toggle_featured, name='toggle_featured'),
    path('admin/reviews/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    
    
]

# ================== MEDIA URLS FOR IMAGE UPLOADS ==================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ================== ERROR HANDLER URLS ==================
handler404 = 'myapp.views.handle_404'
handler500 = 'myapp.views.handle_500'
handler403 = 'myapp.views.handle_403'
handler400 = 'myapp.views.handle_400'