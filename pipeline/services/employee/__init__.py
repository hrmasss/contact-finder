# Employee discovery services
from .base import EmployeeDiscoveryService, EmployeeResult, EmailCandidate
from .gemini import GeminiEmployeeService

__all__ = [
    "EmployeeDiscoveryService",
    "EmployeeResult", 
    "EmailCandidate",
    "GeminiEmployeeService",
]
