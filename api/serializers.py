from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer
from .models import *


class TokenObtainPairSerializer(JwtTokenObtainPairSerializer):
    username_field = get_user_model().USERNAME_FIELD
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['userId'] = user.id
        return token

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'password', 'name', 'image', 'role', 'last_login')


class PasswordSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

class StudentSerializer(serializers.ModelSerializer):
    # interests = serializers.ListField(child=serializers.CharField(max_length=20), required=False)

    class Meta:
        model = Student
        fields = '__all__'

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ('id', 'user', 'subject', 'gender', 'school')

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ('id', 'user', 'phone', 'gender', 'school' )

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = '__all__'

class GoalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goals
        fields = '__all__'

class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = ('id', 'title', 'url', 'coin', 'image')

class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = '__all__'

class CompleteSearializer(serializers.ModelSerializer):
    class Meta:
        model = Complete
        fields = '__all__'
