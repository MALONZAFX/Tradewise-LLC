import os
from django.conf import settings

def paystack_keys(request):
    return {
        'PAYSTACK_PUBLIC_KEY': os.environ.get('PAYSTACK_PUBLIC_KEY', ''),
    }