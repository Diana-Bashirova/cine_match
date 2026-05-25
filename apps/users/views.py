from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    profile = request.user.profile
    return Response({
        'username': request.user.username,
        'preference_vector': profile.preference_vector or {}
    })