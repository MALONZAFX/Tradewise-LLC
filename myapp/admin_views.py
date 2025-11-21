from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test

def is_staff(user):
    return user.is_active and user.is_staff

@login_required
@user_passes_test(is_staff)
def dashboard_home(request):
    return render(request, 'myapp/dashboard.html')
