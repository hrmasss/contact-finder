import time
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .serializers import DiscoveryRequestSerializer, DiscoveryResponseSerializer
from .services.discovery import DiscoveryPipeline


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
    pipeline = DiscoveryPipeline()
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
