from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('about/', include('django.contrib.flatpages.urls')),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
]

urlpatterns += static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

urlpatterns += [

    path('about-author/', views.flatpage, {
        'url': '/about-author/'}, name='about-author'),
    path('about-spec/', views.flatpage, {
        'url': '/about-spec/'}, name='about-spec'),
    path('', include('main.urls')),
]
