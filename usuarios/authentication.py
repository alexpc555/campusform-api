from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Admin, Profesor, Alumno

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        role = validated_token.get("role")

        if not user_id or not role:
            raise AuthenticationFailed("Token inválido: faltan claims.")

        if role == "admin":
            try:
                return Admin.objects.get(id=user_id)
            except Admin.DoesNotExist:
                raise AuthenticationFailed("Admin no existe.")

        if role == "teacher":
            try:
                return Profesor.objects.get(id=user_id)
            except Profesor.DoesNotExist:
                raise AuthenticationFailed("Profesor no existe.")

        if role == "student":
            try:
                return Alumno.objects.get(id=user_id)
            except Alumno.DoesNotExist:
                raise AuthenticationFailed("Alumno no existe.")

        raise AuthenticationFailed("Rol inválido en el token.")