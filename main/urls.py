from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='main'),
    path('api/upload-image', views.upload_image, name='upload image'),
    path('api/get-image-list', views.get_image_list, name='image list'),
    path('api/generate-expiring-link', views.generate_expiring_link, name='generate expiring link'),
]