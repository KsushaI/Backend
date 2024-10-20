"""
URL configuration for Visas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
'''
from django.contrib import admin
from django.urls import path, include
from pages import views

urlpatterns = [
    path('', include('pages.urls')),
    path('order/<int:application_id>/', views.order, name='order'),
    path('add/<int:visa_id>/', views.add, name='add'),
    path('delete/<int:app_id>/', views.delete, name='delete'),
    path('details/<int:visa_id>/', views.details, name='details'),
    path('visas/', views.visas),
    path('admin/', admin.site.urls)
]

'''
from django.contrib import admin
from pages import views
from django.urls import include, path
from rest_framework import routers
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,)
)

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include('pages.urls')),
    path('add/<int:visa_id>/', views.add, name='add'),
    path('delete/<int:app_id>/', views.delete, name='delete'),
    path('order/<int:application_id>/', views.order, name='order'),
    path('details/<int:visa_id>/', views.details, name='details'),
    path('visas/', views.visas),


    path(r'visas_api/', views.VisaList.as_view(), name='visas-list'),
    path(r'visas_api/<int:pk>/', views.VisaDetail.as_view(), name='visas-detail'),
    #path(r'visas_api/<int:pk>/put/', views.put, name='visas-put'),

    path(r'visas_api/<int:pk>/add_to_trolly/', views.add_to_trolly, name='visas-add_to_trolly'),
    path(r'visas_api/<int:pk>/update_pic/', views.update_pic, name='visas-update_pic'),
    path(r'apps_api/', views.AppList.as_view(), name='apps-list'),
    path(r'apps_api/<int:pk>/', views.AppDetail.as_view(), name='apps-detail'),

    path(r'apps_api/<int:pk>/form/', views.form, name='apps-form'),
    path(r'apps_api/<int:pk>/<str:action>/', views.update_application_status, name='apps-update'),

    path(r'apps_visas_api/', views.AppVisaList.as_view(), name='apps_visas-list'),
    path(r'apps_visas_api/<int:pk>/', views.AppVisaList.as_view(), name='apps_visas-put-delete'),

    path(r'users/', views.UserList.as_view(), name='users-list'),
    path(r'users/<int:pk>/', views.UserDetail.as_view(), name='users-detail'),
    path(r'users/<int:pk>/put/', views.user_put, name='users-put'),
    #path(r'authenticate/', views.authenticate, name='authentication'),
    #path(r'deauthorize/', views.deauthorize, name='deauthorization'),

    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),

    path('api/', include(router.urls)),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')
]

