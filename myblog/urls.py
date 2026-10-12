from django.contrib import admin
from django.urls import path,include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,TokenRefreshView
)
from drf_spectacular.views import SpectacularAPIView,SpectacularSwaggerView,SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls')),
    path('api/token/',TokenObtainPairView.as_view(),name="access-token"),
    path('api/token/refresh/',TokenRefreshView.as_view(),name="Refresh-token"),
    path('api/schema/',SpectacularAPIView.as_view(),name="schema"),
    path('api/docs/',SpectacularSwaggerView.as_view(),name="Swagger-UI"),
    path('api/redoc/',SpectacularRedocView.as_view(),name="redoc"),
    
]
