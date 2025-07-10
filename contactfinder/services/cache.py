"""
Simplified cache operations for the contact finder.
No more LangChain tools - just clean functions.
"""

from datetime import timedelta
from django.utils import timezone
from ..models.cache import Company, Employee


def get_company_from_cache(name: str) -> Company | None:
    """Get company from cache if valid."""
    company = Company.find_by_alias(name.strip())
    if company and company.is_cache_valid():
        company.add_search_alias(name.strip())
        return company
    return None


def get_employee_from_cache(company: Company, employee_name: str) -> Employee | None:
    """Get employee from cache if valid."""
    employee = company.employees.filter(full_name__iexact=employee_name).first()
    if employee and employee.is_cache_valid():
        return employee
    return None


def save_company_to_cache(
    name: str,
    primary_domain: str,
    email_patterns: list = None,
    known_emails: list = None,
    all_domains: list = None,
    summary: str = None,
) -> Company:
    """Save or update company in cache."""
    company = Company.find_by_alias(name) or Company(name=name)

    company.primary_domain = primary_domain
    company.email_patterns = email_patterns or []
    company.known_emails = known_emails or []
    company.all_domains = all_domains or []
    company.summary = summary or ""
    company.cache_expires_at = timezone.now() + timedelta(days=90)
    company.last_validated_at = timezone.now()
    company.save()

    company.add_search_alias(name)
    return company


def save_employee_to_cache(
    company: Company,
    full_name: str,
    primary_email: str = "",
    name_variations: dict = None,
    candidate_emails: list = None,
    additional_info: dict = None,
) -> Employee:
    """Save or update employee in cache."""
    employee = company.employees.filter(full_name__iexact=full_name).first()
    if not employee:
        employee = Employee(
            company=company,
            full_name=full_name,
            cache_expires_at=timezone.now() + timedelta(days=30),
        )

    employee.primary_email = primary_email
    employee.name_variations = name_variations or {}
    employee.candidate_emails = candidate_emails or []
    employee.additional_info = additional_info or {}
    employee.last_validated_at = timezone.now()
    employee.save()

    return employee
