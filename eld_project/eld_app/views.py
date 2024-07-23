import requests

from rest_framework.response import Response
from rest_framework.views import APIView
from .utils import detect_hos_violations, validate_hos_with_conditions

from rest_framework.views import APIView
from rest_framework.response import Response
import requests

class BaseELDAPIView(APIView):
    TOKEN_URL = "https://identity-stage.prologs.us/connect/token"
    API_URL = "https://publicapi-stage.prologs.us"
    CLIENT_ID = "9595d560-b813-4cd8-a03a-49b3e28c2dc6"
    CLIENT_SECRET = "uBPCTWyQ9DJT2w6dER6kwXfjNcZJgvOj"

    def get_token(self):
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET
        }
        response = requests.post(self.TOKEN_URL, data=token_data)
        response.raise_for_status()
        return response.json().get('access_token')

    def get_headers(self):
        token = self.get_token()
        return {'Authorization': f'Bearer {token}'}

class ELDDataAPIView(BaseELDAPIView):
    def get(self, request):
        headers = self.get_headers()

        # Fetch ELD Data
        response = requests.get(f"{self.API_URL}/api/v1/drivers", headers=headers)
        response.raise_for_status()

        return Response(response.json())

class ViolationELDDataAPIView(BaseELDAPIView):
    def get(self, request):
        headers = self.get_headers()

        # Fetch ELD Data
        response = requests.get(f"{self.API_URL}/api/v1/drivers", headers=headers)
        response.raise_for_status()

        # Assuming `detect_hos_violations` is a function you have defined elsewhere
        violations = detect_hos_violations(response.json())

        return Response(violations)
    
class VerifyScheduleAPIView(BaseELDAPIView):
    def post(self, request):
        data = request.data
        pickup_time = data.get('pickup_time')
        dropoff_time = data.get('dropoff_time')
        eld_data_list = data.get('eld_data_list')
        driver_type = data.get('driver_type', 'property')  # Default to 'property' if not provided
        
        result = validate_hos_with_conditions(pickup_time, dropoff_time, eld_data_list, driver_type)
        return Response(result)
