from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {'id': self.user.id, 'username': self.user.username, 'is_staff': self.user.is_staff, 'is_superuser': self.user.is_superuser}
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    u = request.user
    return Response({'id':u.id,'username':u.username,'is_staff':u.is_staff,'is_superuser':u.is_superuser})
