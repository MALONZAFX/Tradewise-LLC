import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64
class MpesaC2bCredential:
    consumer_key = 'Ma7I4tMaRYbtVGorPWkYHuq2vWkoKfKA'
    consumer_secret = 'EAAoPehC5z2YvS9F'
    api_URL = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

class LipanaMpesaPpassword:
    lipa_time = datetime.now().strftime('%Y%m%d%H%M%S')
    Business_short_code = "4113409"
    passkey = 'd382f46466860dafe8b8f7632154d9c2b13419e8071594fb8282e39252052d93'
    data_to_encode = Business_short_code + passkey + lipa_time
    online_password = base64.b64encode(data_to_encode.encode())
    decode_password = online_password.decode('utf-8')