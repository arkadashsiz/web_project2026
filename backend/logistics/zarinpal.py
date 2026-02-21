import requests
import json

# Zarinpal Sandbox URLs
ZP_API_REQUEST = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"

MERCHANT_ID = "00000000-0000-0000-0000-000000000000" # Sandbox Merchant ID
CALLBACK_URL = "http://127.0.0.1:8000/api/logistics/bail/verify/"

class ZarinpalService:
    @staticmethod
    def request_payment(amount, description, email=None, mobile=None):
        data = {
            "merchant_id": MERCHANT_ID,
            "amount": amount,
            "currency": "IRT", # Sandbox usually expects Toman or Rial, check docs. Assuming Rial based on prompt.
            "callback_url": CALLBACK_URL,
            "description": description,
            "metadata": {"email": email, "mobile": mobile}
        }
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        
        try:
            response = requests.post(ZP_API_REQUEST, data=json.dumps(data), headers=headers)
            result = response.json()
            
            if result['data']['code'] == 100:
                return {
                    'success': True,
                    'authority': result['data']['authority'],
                    'payment_url': ZP_API_STARTPAY.format(authority=result['data']['authority'])
                }
            return {'success': False, 'error': result['errors']}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def verify_payment(authority, amount):
        data = {
            "merchant_id": MERCHANT_ID,
            "amount": amount,
            "authority": authority
        }
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        
        try:
            response = requests.post(ZP_API_VERIFY, data=json.dumps(data), headers=headers)
            result = response.json()
            
            if result['data']['code'] == 100:
                return {'success': True, 'ref_id': result['data']['ref_id']}
            return {'success': False, 'code': result['data']['code']}
        except Exception as e:
            return {'success': False, 'error': str(e)}
