from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from ..models import Review
from ..forms import AdminReviewForm

def admin_required(function):
    """Decorator to ensure user is admin/staff"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.is_staff or u.is_superuser),
        login_url='/admin/login/'
    )
    return actual_decorator(function)

@login_required
@admin_required
def admin_reviews_dashboard(request):
    """Admin reviews management dashboard"""
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    featured_filter = request.GET.get('featured', 'all')
    search_query = request.GET.get('search', '')
    
    # Start with all reviews
    reviews = Review.objects.all().order_by('-created_at')
    
    # Apply filters
    if status_filter == 'approved':
        reviews = reviews.filter(is_approved=True)
    elif status_filter == 'pending':
        reviews = reviews.filter(is_approved=False)
    
    if featured_filter == 'featured':
        reviews = reviews.filter(is_featured=True)
    elif featured_filter == 'regular':
        reviews = reviews.filter(is_featured=False)
    
    if search_query:
        reviews = reviews.filter(
            models.Q(author_name__icontains=search_query) |
            models.Q(content__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(reviews, 10)  # 10 reviews per page
    page_number = request.GET.get('reviews_page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_reviews = Review.objects.count()
    approved_reviews = Review.objects.filter(is_approved=True).count()
    pending_reviews = Review.objects.filter(is_approved=False).count()
    featured_reviews = Review.objects.filter(is_featured=True).count()
    
    context = {
        'reviews': page_obj,
        'total_reviews': total_reviews,
        'approved_reviews': approved_reviews,
        'pending_reviews': pending_reviews,
        'featured_reviews': featured_reviews,
        'status_filter': status_filter,
        'featured_filter': featured_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@admin_required
def add_review(request):
    """Add review from admin dashboard"""
    if request.method == 'POST':
        form = AdminReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.from_admin = True  # Mark as admin-created
            if not review.is_approved:  # Auto-approve admin reviews by default
                review.is_approved = True
            review.save()
            
            messages.success(request, 'Review added successfully!')
            return redirect('admin_reviews_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminReviewForm()
    
    return render(request, 'admin_dashboard.html', {'review_form': form})

@login_required
@admin_required
def approve_review(request, review_id):
    """Approve a pending review"""
    if request.method == 'POST':
        review = get_object_or_404(Review, id=review_id)
        review.is_approved = True
        review.save()
        
        messages.success(request, f'Review from {review.author_name} approved!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Review approved'})
    
    return redirect('admin_reviews_dashboard')

@login_required
@admin_required
def toggle_featured(request, review_id):
    """Toggle featured status of a review"""
    if request.method == 'POST':
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
    
    return redirect('admin_reviews_dashboard')

@login_required
@admin_required
def delete_review(request, review_id):
    """Delete a review"""
    if request.method == 'POST':
        review = get_object_or_404(Review, id=review_id)
        author_name = review.author_name
        review.delete()
        
        messages.success(request, f'Review from {author_name} deleted!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Review deleted'})
    
    return redirect('admin_reviews_dashboard')

@login_required
@admin_required
def bulk_approve_reviews(request):
    """Approve all pending reviews"""
    if request.method == 'POST':
        pending_reviews = Review.objects.filter(is_approved=False)
        count = pending_reviews.count()
        
        pending_reviews.update(is_approved=True)
        
        messages.success(request, f'{count} pending reviews approved!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'{count} reviews approved'})
    
    return redirect('admin_reviews_dashboard')