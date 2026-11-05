from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import plan_eld_trip

class PlanTripView(APIView):
    def post(self, request):
        try:
            current_loc = request.data.get('current_location')
            pickup_loc = request.data.get('pickup_location')
            dropoff_loc = request.data.get('dropoff_location')
            cycle_used = float(request.data.get('cycle_used', 0.0))

            if not current_loc or not pickup_loc or not dropoff_loc:
                return Response(
                    {'error': 'current_location, pickup_location, and dropoff_location are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = plan_eld_trip(current_loc, pickup_loc, dropoff_loc, cycle_used)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)