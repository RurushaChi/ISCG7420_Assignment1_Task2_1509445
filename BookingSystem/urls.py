"""
URL configuration for BookingSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from booking import views
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Redirect root to /booking/
    path("", RedirectView.as_view(url="/booking/", permanent=False)),

    # All standard site pages (HTML views) from booking app
    path("booking/", include("booking.urls")),

    # REST API endpoints (Django REST Framework + JWT)
    path("api/", include("booking.api_urls")),

    # Django admin
    path("admin/", admin.site.urls),
]

