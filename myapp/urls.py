# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ================== WEBSITE FRONTEND URLS ==================
    path('', views.index, name='index'),
    path('explore/', views.explore, name='explore'),
    path('market/', views.market_hub, name='market_hub'),
    path('trade/', views.trade, name='trade_desk'),
    path('contact/', views.contact, name='contact'),
    path('account/', views.account, name='account'),
    path('payment/', views.payment, name='payment'),

    # ================== WEBSITE AUTHENTICATION URLS ==================
    path('login/', views.login_view, name='login_view'),
    path('signup/', views.signup, name='signup'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('logout/', views.logout_view, name='logout_view'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # ================== ADMIN AUTHENTICATION URLS ==================
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('direct-admin/', views.direct_admin, name='direct_admin'),
    
    # ================== CONTENT PAGES URLS ==================
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('shop/', views.shop, name='shop'),

    # ================== PAYMENT URLS ==================
    path('initialize-payment/', views.initialize_payment, name='initialize_payment'),
    path('verify-payment/<str:reference>/', views.verify_payment, name='verify_payment'),
    
    # ================== SERVICE REQUEST URLS ==================
    path('submit-service-request/', views.submit_service_request, name='submit_service_request'),
    
    # ================== STRATEGIES URLS ==================
    path('market/strategies/free/', views.free_strategies, name='free_strategies'),
    path('activate-strategies/', views.activate_all_strategies, name='activate_strategies'),
    path('market/strategies/premium/', views.premium_strategies, name='premium_strategies'),
    path('market/strategies/<int:strategy_id>/', views.strategy_detail, name='strategy_detail'),

    # ================== SIGNALS URLS ==================
    path('market/signals/free/', views.free_signals, name='free_signals'),
    path('activate-signals/', views.activate_all_signals, name='activate_signals'),
    
    # ================== SOFTWARE URLS ==================
    path('software/free/', views.free_software, name='free_software'),
    path('software/premium/', views.premium_software, name='premium_software'),
    path('software/<int:software_id>/', views.software_detail, name='software_detail'),
    path('ajax/track-download/<int:software_id>/', views.track_software_download, name='track_software_download'),
    path('admin/activate-all-software/', views.activate_all_software, name='activate_all_software'),

    # ================== SERVICE PAYMENT URLS ==================
    path('initialize-service-payment/', views.initialize_service_payment, name='initialize_service_payment'),
    path('verify-service-payment/<str:reference>/', views.verify_service_payment, name='verify_service_payment'),

    # ================== SEPARATE PAYMENT URLS ==================
    path('initialize-plan-payment/', views.initialize_plan_payment, name='initialize_plan_payment'),

    # ================== MERCHANDISE URLS ==================
    path('merchandise/process-payment/', views.initialize_merchandise_payment, name='process_merchandise_payment'),
    path('verify-merchandise-payment/<str:reference>/', views.verify_merchandise_payment, name='verify_merchandise_payment'),

    # ================== NEW BLOG & REVIEWS MANAGEMENT URLS ==================
    
    # Review Submission & API URLs
    path('submit-review/', views.submit_review, name='submit_review'),
    path('api/reviews/', views.get_approved_reviews, name='get_reviews'),
    path('api/blogs/', views.get_published_blogs, name='get_blogs'),
    
    # Admin Review Management URLs
    path('admin/approve-review/<int:review_id>/', views.approve_review, name='approve_review'),
    path('admin/feature-review/<int:review_id>/', views.toggle_review_featured, name='toggle_review_featured'),
    path('admin/delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('admin/approve-all-reviews/', views.approve_all_pending_reviews, name='approve_all_reviews'),
    
    # Admin Blog Management URLs
    path('admin/add-blog/', views.add_blog_post, name='add_blog_post'),
    path('admin/edit-blog/<int:post_id>/', views.edit_blog_post, name='edit_blog_post'),
    path('admin/delete-blog/<int:post_id>/', views.delete_blog_post, name='delete_blog_post'),
    path('blog/', views.blog_list, name='blog'),  
    
    # Service Payment Admin URLs
    path('admin/send-onboarding-email/<int:payment_id>/', views.send_service_onboarding_email, name='send_onboarding_email'),
    path('admin/add-manual-payment/<int:payment_id>/', views.add_manual_payment, name='add_manual_payment'),

    # ================== NEW REFERRAL MANAGEMENT URLS ==================
    path('approve-referral/', views.approve_referral, name='approve_referral'),
    path('admin/approve-referral/<int:referral_id>/', views.approve_referral, name='approve_referral_by_id'),
    path('admin/reject-referral/<int:referral_id>/', views.reject_referral, name='reject_referral'),
    path('admin/approve-all-referrals/', views.approve_all_pending_referrals, name='approve_all_referrals'),
    path('admin/bulk-approve-referrals/', views.bulk_approve_referrals, name='bulk_approve_referrals'),
    
    # ================== NEW AFFILIATE DATA URLS ==================
    path('get-affiliate-data/', views.get_affiliate_data, name='get_affiliate_data'),
    path('get-weekly-number/', views.get_weekly_number, name='get_weekly_number'),
    path('request-payout/', views.request_payout, name='request_payout'),
    
    # ================== EMAIL TESTING URLS ==================
    path('test-email/', views.test_email_delivery, name='test_email'),
    path('test-email-setup/', views.test_email_setup, name='test_email_setup'),
    path('quick-email-test/', views.quick_email_test, name='quick_email_test'),
    path('test-multiple-emails/', views.test_multiple_emails, name='test_multiple_emails'),
    
    # ================== CARD DATA API ==================
    path('get-card-data/', views.get_card_data, name='get_card_data'),

    # ================== SERVICE REQUEST ACTION URLS ==================
path('admin/update-request-status/', views.update_request_status_traditional, name='update_request_status'),
path('admin/delete-request/<int:request_id>/', views.delete_request, name='delete_request'),
path('admin/view-request/<int:request_id>/', views.view_request_details, name='view_request_details'),

# ================== AJAX ENDPOINTS FOR BUTTONS ==================
path('ajax/update-request-status/', views.ajax_update_request_status, name='ajax_update_request_status'),
path('ajax/delete-request/', views.ajax_delete_request, name='ajax_delete_request'),


# ================== COINS TRANSACTIONS URL==================
    path('initialize-coin-buy/', views.initialize_coin_buy, name='initialize_coin_buy'),
    path('submit-coin-sell-request/', views.submit_coin_sell_request, name='submit_coin_sell_request'),
    path('verify-coin-payment/<str:reference>/', views.verify_coin_payment, name='verify_coin_payment'),
    path('admin/update-coin-transaction/', views.update_coin_transaction_status, name='update_coin_transaction_status'),
    path('debug-email-templates/', views.debug_email_templates, name='debug_email_templates'),
   path('test-admin-coin-actions/', views.test_admin_coin_actions, name='test_admin_coin_actions'),
   path('admin-process-form/', views.process_admin_form, name='process_admin_form'),
   path('admin/ajax/users-data/', views.ajax_users_data, name='ajax_users_data'),
    
]