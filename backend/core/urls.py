from django.contrib import admin
from django.urls import path
from eld_planner.views import PlanTripView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/plan-trip/', PlanTripView.as_view(), name='plan_trip'),
]
