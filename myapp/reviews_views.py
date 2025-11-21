from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from ..models import Review
from ..forms import ReviewForm
import json

def reviews_api(request):
    """API endpoint to fetch approved reviews for frontend"""
    if request.method == 'GET':
        # Get only approved reviews for public display
        reviews = Review.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')
        
        # Convert to JSON-serializable format
        reviews_data = []
        for review in reviews:
            reviews_data.append({
                'id': review.id,
                'author_name': review.author_name,
                'user_role': review.user_role,
                'rating': review.rating,
                'content': review.content,
                'image_url': review.image.url if review.image else None,
                'is_featured': review.is_featured,
                'created_at': review.created_at.strftime('%b %d, %Y'),
            })
        
        # Calculate statistics
        total_reviews = reviews.count()
        average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        return JsonResponse({
            'success': True,
            'reviews': reviews_data,
            'statistics': {
                'total_reviews': total_reviews,
                'average_rating': round(average_rating, 1),
            }
        })
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@csrf_exempt
@require_http_methods(["POST"])
def submit_review(request):
    """Handle review submission from frontend"""
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            review.from_admin = False  # Mark as user-submitted
            review.is_approved = False  # Require admin approval
            review.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your review! It will be published after approval.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please check your form and try again.',
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def review_statistics(request):
    """Get review statistics for admin dashboard"""
    if request.user.is_authenticated and request.user.is_staff:
        total_reviews = Review.objects.count()
        approved_reviews = Review.objects.filter(is_approved=True).count()
        pending_reviews = Review.objects.filter(is_approved=False).count()
        featured_reviews = Review.objects.filter(is_featured=True).count()
        
        return JsonResponse({
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'pending_reviews': pending_reviews,
            'featured_reviews': featured_reviews,
        })
    
    return JsonResponse({'error': 'Unauthorized'}, status=403)