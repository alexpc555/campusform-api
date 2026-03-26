from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class Alumno(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.contrasena and not self.contrasena.startswith("pbkdf2_"):
            self.contrasena = make_password(self.contrasena)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.contrasena)
    
    @property
    def is_authenticated(self):
        return True

class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.contrasena and not self.contrasena.startswith("pbkdf2_"):
            self.contrasena = make_password(self.contrasena)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.contrasena)
    
    @property
    def is_authenticated(self):
        return True

class Admin(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.contrasena and not self.contrasena.startswith("pbkdf2_"):
            self.contrasena = make_password(self.contrasena)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.contrasena)
    
    @property
    def is_authenticated(self):
        return True

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    creada_por = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='categorias')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre
    
    @property
    def post_count(self):
        return self.posts.count() if hasattr(self, 'posts') else 0

class Post(models.Model):
    titulo = models.CharField(max_length=150)
    contenido = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='posts')
    autor_alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    autor_profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    autor_admin = models.ForeignKey(Admin, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')
    etiquetas = models.CharField(max_length=500, blank=True, null=True)
    vistas = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo

    @property
    def autor(self):
        if self.autor_alumno:
            return self.autor_alumno
        elif self.autor_profesor:
            return self.autor_profesor
        elif self.autor_admin:
            return self.autor_admin
        return None

    @property
    def autor_nombre(self):
        autor = self.autor
        return autor.nombre if autor else 'Usuario desconocido'

    @property
    def autor_tipo(self):
        if self.autor_alumno:
            return 'student'
        elif self.autor_profesor:
            return 'teacher'
        elif self.autor_admin:
            return 'admin'
        return None