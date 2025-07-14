from django.urls import path
from . import api

app_name = "pipeline"

urlpatterns = [
    path("discover-company/", api.discover_company_domains, name="discover-company"),
    path("discover-employee/", api.discover_employees, name="discover-employee"),
]
