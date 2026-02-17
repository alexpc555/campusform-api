from rest_framework import serializers
from .models import Alumno, Profesor

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    role = serializers.ChoiceField(choices=["student", "teacher"])

    def validate_email(self, value):
        value = value.strip().lower()
        if Alumno.objects.filter(correo=value).exists() or Profesor.objects.filter(correo=value).exists():
            raise serializers.ValidationError("Ese correo ya está registrado.")
        return value

    def create(self, validated_data):
        name = validated_data["name"].strip()
        email = validated_data["email"].strip().lower()
        password = validated_data["password"]
        role = validated_data["role"]

        if role == "student":
            return Alumno.objects.create(nombre=name, correo=email, contrasena=password)
        return Profesor.objects.create(nombre=name, correo=email, contrasena=password)
