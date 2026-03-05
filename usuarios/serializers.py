from rest_framework import serializers
from .models import Alumno, Profesor, Admin, Categoria

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    role = serializers.ChoiceField(choices=["student", "teacher", "admin"])

    def validate_email(self, value):
        value = value.strip().lower()
        if (Alumno.objects.filter(correo=value).exists() or 
            Profesor.objects.filter(correo=value).exists() or
            Admin.objects.filter(correo=value).exists()):
            raise serializers.ValidationError("Ese correo ya está registrado.")
        return value

    def create(self, validated_data):
        name = validated_data["name"].strip()
        email = validated_data["email"].strip().lower()
        password = validated_data["password"]
        role = validated_data["role"]

        if role == "student":
            return Alumno.objects.create(nombre=name, correo=email, contrasena=password)
        elif role == "teacher":
            return Profesor.objects.create(nombre=name, correo=email, contrasena=password)
        else:  # admin
            return Admin.objects.create(nombre=name, correo=email, contrasena=password)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["student", "teacher", "admin"], required=False)

    def validate(self, data):
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role')

        # Buscar usuario por email
        user = None
        user_model = None
        
        # Intentar encontrar en Alumno
        try:
            user = Alumno.objects.get(correo=email)
            user_model = 'student'
        except Alumno.DoesNotExist:
            try:
                user = Profesor.objects.get(correo=email)
                user_model = 'teacher'
            except Profesor.DoesNotExist:
                try:
                    user = Admin.objects.get(correo=email)
                    user_model = 'admin'
                except Admin.DoesNotExist:
                    raise serializers.ValidationError({"email": "Credenciales inválidas"})

        # Verificar contraseña
        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Credenciales inválidas"})

        # Verificar rol si se proporcionó
        if role and role != user_model:
            raise serializers.ValidationError({"role": "El tipo de usuario no coincide"})

        data['user'] = user
        data['user_model'] = user_model
        return data

class CategoriaSerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True)
    creada_por_nombre = serializers.CharField(source='creada_por.nombre', read_only=True)
    
    class Meta:
        model = Categoria
        fields = [
            'id', 'nombre', 'descripcion', 
            'post_count', 'creada_por', 'creada_por_nombre',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'creada_por', 'fecha_creacion', 'fecha_actualizacion']