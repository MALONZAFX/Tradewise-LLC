# dict/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from myapp import views

urlpatterns = [
    # Catch ALL old admin URLs first with redirects
    path('admin/login/', RedirectView.as_view(url='/admin-login/', permanent=True)),
    path('admin/logout/', RedirectView.as_view(url='/admin-login/', permanent=True)),
    path('admin/', RedirectView.as_view(url='/admin-login/', permanent=True)),
    
    # Include your app URLs
    path('', include('myapp.urls')),
    
    # Django admin (optional)
    path('django-admin/', admin.site.urls),

    path('test-sendgrid-now/', views.test_sendgrid_now, name='test_sendgrid_now'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error handlers
handler404 = 'myapp.views.handler404'
handler500 = 'myapp.views.handler500'