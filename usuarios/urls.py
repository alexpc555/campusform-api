from django.urls import path
from .views import (
    RegisterView, LoginView, CategoriaListCreateView, CategoriaDetailView,
    UsuarioListCreateView, UsuarioDetailView, PostListCreateView,
    MisPostsView, PostDetailView, ComentarioListCreateView,
    ComentarioDetailView, ReporteListCreateView, ReporteDetailView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Categorías
    path('categorias/', CategoriaListCreateView.as_view(), name='categoria-list'),
    path('categorias/<int:pk>/', CategoriaDetailView.as_view(), name='categoria-detail'),

    # Usuarios
    path('usuarios/', UsuarioListCreateView.as_view(), name='usuario-list'),
    path('usuarios/<int:pk>/', UsuarioDetailView.as_view(), name='usuario-detail'),

    # Posts
    path('posts/', PostListCreateView.as_view(), name='post-list'),
    path('posts/mis-posts/', MisPostsView.as_view(), name='mis-posts'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),

    # Comentarios
    path('comentarios/', ComentarioListCreateView.as_view(), name='comentario-list'),
    path('comentarios/<int:pk>/', ComentarioDetailView.as_view(), name='comentario-detail'),

    # Reportes
    path('reportes/', ReporteListCreateView.as_view(), name='reporte-list'),
    path('reportes/<int:pk>/', ReporteDetailView.as_view(), name='reporte-detail'),
]