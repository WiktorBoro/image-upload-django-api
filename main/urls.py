from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view

urlpatterns = [
    path('', views.home, name='main'),
    path('api/upload-image', views.upload_image, name='upload image'),
    path('api/get-image-list', views.get_image_list, name='image list'),
    path('api/generate-expiring-link', views.generate_expiring_link, name='generate expiring link'),
    path('api_schema', get_schema_view(title='Api schema'), name='api_schema'),
    path('swagger', TemplateView.as_view(template_name='swagger.html',
                                         extra_context={'schema_url': 'api_schema'}
                                        ), name='swagger-ui'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
