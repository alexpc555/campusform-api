from django.db import models
from django.contrib.auth.hashers import make_password, check_password

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
        """Retorna el número de publicaciones en esta categoría"""
        # Si tienes un modelo Post, descomenta esto:
        # from .models import Post
        # return self.posts.count()
        return 0  # Temporalmente retorna 0