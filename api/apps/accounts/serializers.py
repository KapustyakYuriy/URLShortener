from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError

class RegisterSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True)

	class Meta:
		model = User
		fields = ["username", "password"]
		extra_kwargs = {
			 "username": {"validators": []},
		}

	def validate_password(self, value):
		try:
			validate_password(value)

		except ValidationError as e:
			raise serializers.ValidationError(e.messages)
		
		return value
	
	def create(self, validated_data):
		try:
			return User.objects.create_user(**validated_data)
		except IntegrityError:
			raise serializers.ValidationError({"username": ["A user with that username already exists."]})

