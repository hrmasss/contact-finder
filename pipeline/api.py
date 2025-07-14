import time
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .serializers import (
    DiscoveryRequestSerializer,
    DiscoveryResponseSerializer,
    EmployeeDiscoveryRequestSerializer,
    EmployeeDiscoveryResponseSerializer,
)
from .services.company_discovery import CompanyDiscoveryPipeline
from .services.employee_discovery import EmployeeDiscoveryPipeline


@extend_schema(
    request=DiscoveryRequestSerializer, responses={200: DiscoveryResponseSerializer}
)
@api_view(["POST"])
@permission_classes([AllowAny])
def discover_company_domains(request):
    """Discover company domains and email patterns."""
    serializer = DiscoveryRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Track query time
    start_time = time.time()

    # Run discovery pipeline
    pipeline = CompanyDiscoveryPipeline()
    companies = pipeline.discover(
        company_query=serializer.validated_data["company_query"],
        search_level=serializer.validated_data["search_level"],
        additional_info=serializer.validated_data.get("additional_info", {}),
        force_refresh=serializer.validated_data["force_refresh"],
    )

    # Calculate query time
    query_time_ms = int((time.time() - start_time) * 1000)

    # Mark cached results
    from_cache = False
    if companies:
        for company in companies:
            if hasattr(company, "last_validated_at") and company.last_validated_at:
                # If validated recently, it's likely from cache
                time_since_validation = (
                    time.time() - company.last_validated_at.timestamp()
                )
                if time_since_validation < 300:  # 5 minutes
                    company._from_cache = True
                    from_cache = True

    # Serialize results
    response_data = {
        "companies": companies,
        "total_found": len(companies),
        "search_level": serializer.validated_data["search_level"],
        "from_cache": from_cache,
        "query_time_ms": query_time_ms,
    }

    # Use the response serializer to ensure proper schema
    response_serializer = DiscoveryResponseSerializer(response_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=EmployeeDiscoveryRequestSerializer,
    responses={200: EmployeeDiscoveryResponseSerializer},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def discover_employees(request):
    """Discover employees with email candidates."""
    serializer = EmployeeDiscoveryRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Track query time
    start_time = time.time()

    # Run employee discovery pipeline
    pipeline = EmployeeDiscoveryPipeline()
    employees = pipeline.discover(
        employee_query=serializer.validated_data["employee_query"],
        company_query=serializer.validated_data.get("company_query"),
        company_id=serializer.validated_data.get("company_id"),
        search_level=serializer.validated_data["search_level"],
        additional_info=serializer.validated_data.get("additional_info", {}),
        force_refresh=serializer.validated_data.get("force_refresh", False),
    )

    # Calculate query time
    query_time_ms = int((time.time() - start_time) * 1000)

    # Mark cached results
    from_cache = False
    if employees:
        for employee in employees:
            if hasattr(employee, "last_validated_at") and employee.last_validated_at:
                # If validated recently, it's likely from cache
                time_since_validation = (
                    time.time() - employee.last_validated_at.timestamp()
                )
                if time_since_validation < 300:  # 5 minutes
                    employee._from_cache = True
                    from_cache = True

    # Add best email methods to each employee
    for employee in employees:
        employee.best_email = employee.get_best_email()
        employee.best_emails = employee.get_best_emails(limit=3)

    # Serialize results
    response_data = {
        "employees": employees,
        "total_found": len(employees),
        "search_level": serializer.validated_data["search_level"],
        "from_cache": from_cache,
        "query_time_ms": query_time_ms,
    }

    # Use the response serializer to ensure proper schema
    response_serializer = EmployeeDiscoveryResponseSerializer(response_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)
