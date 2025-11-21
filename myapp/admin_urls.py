from django.urls import path
from . import views

urlpatterns = [
    # Admin Authentication
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Main Admin Dashboard - EMPTY PATH for /myadmin/
    path('', views.admin_dashboard, name='admin_dashboard'),
    
    # Content Management URLs
    path('strategies/', views.admin_trading_strategies, name='admin_strategies'),
    path('signals/', views.admin_trading_signals, name='admin_signals'),
    path('classes/', views.admin_trading_classes, name='admin_classes'),
    path('research/', views.admin_research_materials, name='admin_research'),
    path('services/', views.admin_services_management, name='admin_services'),
    path('blog/', views.admin_blog_management, name='admin_blog'),
    path('merchandise/', views.admin_merchandise_management, name='admin_merchandise'),
    
    # Requests Management URLs
    path('requests/all/', views.admin_all_requests, name='admin_all_requests'),
    path('requests/classes/', views.admin_class_requests, name='admin_class_requests'),
    path('requests/signals/', views.admin_signal_requests, name='admin_signal_requests'),
    
    # User Management URLs
    path('users/', views.admin_user_management, name='admin_users'),
    path('accounts/', views.admin_account_management, name='admin_accounts'),
    
    # API Endpoints for Admin Dashboard
    path('api/stats/', views.admin_get_dashboard_stats, name='admin_api_stats'),
    path('api/strategies/save/', views.admin_save_strategy, name='admin_save_strategy'),
]