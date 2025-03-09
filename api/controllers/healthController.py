from rest_framework.response import Response
from rest_framework.views import APIView
from django.urls import path

class HealthView(APIView):
    def get(self, request):
        return Response({"message": "Hello!"}, status=200)

urlpatterns = [
    path('health', HealthView.as_view(), name='health')
]
