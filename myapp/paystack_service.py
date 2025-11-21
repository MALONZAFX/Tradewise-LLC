import requests
import json
from django.conf import settings

class PaystackService:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.public_key = settings.PAYSTACK_PUBLIC_KEY
        self.base_url = "https://api.paystack.co"
    
    def initialize_transaction(self, email, amount, reference, callback_url=None, metadata=None):
        url = f"{self.base_url}/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }
        
        data = {
            "email": email,
            "amount": int(amount * 100),  # Convert to kobo
            "reference": reference,
        }
        
        if callback_url:
            data["callback_url"] = callback_url
            
        if metadata:
            data["metadata"] = metadata
            
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.json()
        except Exception as e:
            return {"status": False, "message": str(e)}
    
    def verify_transaction(self, reference):
        url = f"{self.base_url}/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
        }
        
        try:
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            return {"status": False, "message": str(e)}