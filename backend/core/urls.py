from django.contrib import admin
from django.urls import path
from eld_planner.views import PlanTripView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', PlanTripView.as_view(), name='root_plan_trip'),
    path('plan-trip/', PlanTripView.as_view(), name='plan_trip'),
    path('api/plan-trip/', PlanTripView.as_view(), name='api_plan_trip'),
]