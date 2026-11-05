from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import plan_eld_trip

class PlanTripView(APIView):
    def post(self, request):
        try:
            curr = request.data.get('current_location')
            pick = request.data.get('pickup_location')
            drop = request.data.get('dropoff_location')
            cycle = float(request.data.get('current_cycle_used', 0.0))

            if not curr or not pick or not drop:
                return Response(
                    {'error': 'All location fields are required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            res = plan_eld_trip(curr, pick, drop, cycle)
            return Response(res, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error processing trip: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)