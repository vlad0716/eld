from django.urls import path
from . import views

urlpatterns = [
    path('eld_data', views.ELDDataAPIView.as_view(), name='eld_data'),
    path('violation_eld_data', views.ViolationELDDataAPIView.as_view(), name='violation_eld_data'),
    path('verify_schedule', views.VerifyScheduleAPIView.as_view(), name="verify_schedule")
]

