from django.contrib import admin
from common.admin import BaseModelAdmin
from .models.cache import Company, Employee

@admin.register(Company)
class CompanyAdmin(BaseModelAdmin):
    list_display = ("name", "primary_domain", "cache_expires_at", "last_validated_at")
    list_filter = ("cache_expires_at",)
    search_fields = ("name", "primary_domain", "search_aliases")

@admin.register(Employee)
class EmployeeAdmin(BaseModelAdmin):
    list_display = ("full_name", "company", "primary_email", "cache_expires_at")
    list_filter = ("cache_expires_at",)
    search_fields = ("full_name", "company__name")
