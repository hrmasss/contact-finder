from ..services import find_contact
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from ..serializers import (
    ContactFinderRequestSerializer,
    ContactFinderResponseSerializer,
)


@extend_schema(
    request=ContactFinderRequestSerializer,
    responses=ContactFinderResponseSerializer,
    description="Find contact email for a person at a company",
)
class ContactFinderAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=ContactFinderRequestSerializer,
        responses=ContactFinderResponseSerializer,
    )
    def post(self, request, *args, **kwargs):
        """
        API endpoint to find contact email for a person at a company.

        POST /api/contactfinder/find/
        {
            "company_query": "GitHub",
            "person_name": "John Smith",
            "use_cache": true
        }
        """
        try:
            # Validate request data
            req_serializer = ContactFinderRequestSerializer(data=request.data)
            req_serializer.is_valid(raise_exception=True)
            validated = req_serializer.validated_data

            # Execute flow
            result = find_contact(**validated)

            # Serialize response
            resp_serializer = ContactFinderResponseSerializer(data=result)
            resp_serializer.is_valid(raise_exception=True)
            return Response(
                {"success": True, "data": resp_serializer.data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
