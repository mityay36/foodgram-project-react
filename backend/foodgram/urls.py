from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls'))
]

schema_view = get_schema_view(
    openapi.Info(
        title="Foodgram API",
        default_version='v1',
        description="Документация проекта Foodgram",
        # terms_of_service="URL страницы с пользовательским соглашением",
        contact=openapi.Contact(email="admin@fodgram.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    url(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0), name='schema-json'
    ),
    url(
        r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
    ),
    url(
        r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
