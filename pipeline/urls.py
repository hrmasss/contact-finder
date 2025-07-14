from django.urls import path
from . import api

app_name = "pipeline"

urlpatterns = [
    path("discover/", api.discover_company_domains, name="discover"),
]
