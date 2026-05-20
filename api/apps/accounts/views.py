from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

class RegisterView(APIView):
	permission_classes = [AllowAny]

	def post(self, request: Request) -> Response:
		username = request.data.get('username')
		password = request.data.get('password')

		if not username or not password:
			return Response(
				{"error": "username and password are required"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try: 
			validate_password(password)
		except ValidationError as e:
			return Response(
				{"error": e.messages}, 
				status=status.HTTP_400_BAD_REQUEST
			)

		if User.objects.filter(username=username).exists():
			return Response(
				{"error": "username already taken"},
				status=status.HTTP_400_BAD_REQUEST,
			)
		
		user = User.objects.create_user(username=username, password=password)
		refresh = RefreshToken.for_user(user)
		return Response(
			{
				"message": "user created successfully",
				"access": str(refresh.access_token),
				"refresh": str(refresh),
			}, 
			status=status.HTTP_201_CREATED
		)