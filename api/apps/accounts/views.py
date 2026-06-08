from loguru import logger
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

from apps.accounts.serializers import RegisterSerializer

class RegisterView(APIView):
	permission_classes = [AllowAny]

	def post(self, request: Request) -> Response:
		serializer = RegisterSerializer(data=request.data)

		serializer.is_valid(raise_exception=True)
		user = serializer.save()

		logger.info("user registered | username={}", user.username)
		refresh = RefreshToken.for_user(user)

		return Response(
			{
				"message": "user created successfully",
				"access": str(refresh.access_token),
				"refresh": str(refresh),
			},
			status=status.HTTP_201_CREATED,
		)