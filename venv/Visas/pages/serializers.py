from .models import Visa, Application, Application_Visa
from django.contrib.auth.models import User
from rest_framework import serializers


class VisaSerializer(serializers.ModelSerializer):
    # StringRelatedField вернет строковое представление объекта, то есть его имя
    creator = serializers.StringRelatedField(read_only=True)

    class Meta:
        # Модель, которую мы сериализуем
        model = Visa
        # Поля, которые мы сериализуем
        fields = ["pk", "type", "price", "url", "status", "description", "creator"]


class UserSerializer(serializers.ModelSerializer):
    # visa_set = VisaSerializer(many=True, read_only=True)
    class Meta:
        model = User
        fields = ["id", "username", "password", "is_staff", "is_superuser"]


class ApplicationSerializer(serializers.ModelSerializer):
    creator = serializers.StringRelatedField()
    moderator = serializers.StringRelatedField()

    # Custom field to display username
    class Meta:
        model = Application
        fields = ["id", "status", "creation_date", "formation_date", "completion_date", "creator", "moderator",
                  "start_date", "duration", "total"]


class ApplicationVisaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application_Visa
        fields = ["id", "app", "visa", "fio"]
