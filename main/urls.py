from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.static import serve


schema_view = get_schema_view(
   openapi.Info(
      title="Image upload API",
      default_version='v1',
      description="Image upload API book",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="w.borowicz4@gmail.pl"),
      license=openapi.License(name="MIT", url="https://opensource.org/licenses/MIT"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   authentication_classes=()
)

urlpatterns = [
    path('api/upload-image', views.UploadImage.as_view(), name='upload image'),
    path('api/get-image-list', views.GetImageList.as_view(), name='image list'),
    path('api/generate-expiring-link', views.GenerateExpiringLink.as_view(), name='generate expiring link'),
    path('swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    re_path(r'^images/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
