from django.urls import path
from contactfinder.api import ContactFinderAPIView

urlpatterns = [
    path("find/", ContactFinderAPIView.as_view(), name="find_contact"),
]
