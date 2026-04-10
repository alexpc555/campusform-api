from rest_framework import serializers
from .models import Alumno, Profesor, Admin, Categoria,Post, Comentario,Reporte

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
    creador_nombre = serializers.ReadOnlyField()
    creador_tipo = serializers.ReadOnlyField()
    post_count = serializers.ReadOnlyField()

    class Meta:
        model = Categoria
        fields = [
            'id',
            'nombre',
            'descripcion',
            'creador_nombre',
            'creador_tipo',
            'post_count',
            'fecha_creacion',
            'fecha_actualizacion',
        ]


#serializer nuevos 25/03/2026
class PostSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    autor_nombre = serializers.CharField(read_only=True)
    autor_tipo = serializers.CharField(read_only=True)
    comentarios_count = serializers.IntegerField(source='comentarios.count', read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'titulo', 'contenido', 'categoria', 'categoria_nombre',
            'autor_nombre', 'autor_tipo', 'etiquetas', 'vistas',
            'comentarios_count', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion', 'vistas', 'comentarios_count']
    
    def validate(self, data):
        request = self.context.get('request')
        if request and request.user:
            return data
        raise serializers.ValidationError("Usuario no autenticado")

class ComentarioSerializer(serializers.ModelSerializer):
    autor_nombre = serializers.CharField(read_only=True)
    autor_id = serializers.SerializerMethodField()
    autor_tipo = serializers.SerializerMethodField()

    class Meta:
        model = Comentario
        fields = [
            'id',
            'contenido',
            'post',
            'autor_nombre',
            'autor_id',
            'autor_tipo',
            'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']

    def get_autor_id(self, obj):
        autor = obj.autor
        return autor.id if autor else None

    def get_autor_tipo(self, obj):
        if obj.autor_alumno:
            return 'student'
        if obj.autor_profesor:
            return 'teacher'
        if obj.autor_admin:
            return 'admin'
        return None

    def validate(self, data):
        request = self.context.get('request')
        if request and request.user:
            return data
        raise serializers.ValidationError("Usuario no autenticado")


class ReporteSerializer(serializers.ModelSerializer):
    post_titulo = serializers.CharField(source='post.titulo', read_only=True)
    motivo_display = serializers.CharField(source='get_motivo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    autor_nombre = serializers.CharField(read_only=True)

    class Meta:
        model = Reporte
        fields = [
            'id', 'post', 'post_titulo', 'motivo', 'motivo_display',
            'razon', 'estado', 'estado_display', 'autor_nombre', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']