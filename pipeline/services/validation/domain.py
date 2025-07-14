"""
Domain validation services for company email domain verification.

This module provides comprehensive domain validation including:
- MX record verification
- DNS resolution checks 
- Domain format validation
- Confidence scoring based on validation results
"""

import dns.resolver
import socket
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DomainValidationResult:
    """Result from domain validation."""
    
    domain: str
    is_valid: bool
    confidence_penalty: float  # 0.0 to 1.0 multiplier for confidence
    validation_status: str  # 'valid', 'no_mx', 'no_dns', 'invalid_format', 'error'
    details: Dict[str, Any]  # Additional validation metadata
    checks_performed: List[str]  # List of validation checks that were run


class DomainValidator(ABC):
    """Base interface for domain validation."""
    
    @abstractmethod
    def validate(self, domain: str) -> DomainValidationResult:
        """Validate a domain and return validation result."""
        pass


class MXRecordValidator(DomainValidator):
    """Validates domains by checking MX records."""
    
    def validate(self, domain: str) -> DomainValidationResult:
        """Check if domain has valid MX records."""
        checks_performed = ['mx_record']
        details = {}
        
        try:
            # Query MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_list = [str(mx) for mx in mx_records]
            
            details['mx_records'] = mx_list
            details['mx_count'] = len(mx_list)
            
            if mx_list:
                logger.debug(f"Domain {domain} has {len(mx_list)} MX records")
                return DomainValidationResult(
                    domain=domain,
                    is_valid=True,
                    confidence_penalty=1.0,  # No penalty
                    validation_status='valid',
                    details=details,
                    checks_performed=checks_performed
                )
            else:
                logger.warning(f"Domain {domain} has no MX records")
                return DomainValidationResult(
                    domain=domain,
                    is_valid=False,
                    confidence_penalty=0.1,  # Heavy penalty - 90% reduction
                    validation_status='no_mx',
                    details=details,
                    checks_performed=checks_performed
                )
                
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain {domain} does not exist (NXDOMAIN)")
            details['error'] = 'Domain does not exist'
            return DomainValidationResult(
                domain=domain,
                is_valid=False,
                confidence_penalty=0.05,  # Very heavy penalty - 95% reduction
                validation_status='no_dns',
                details=details,
                checks_performed=checks_performed
            )
            
        except dns.resolver.NoAnswer:
            logger.warning(f"Domain {domain} has no MX records")
            details['error'] = 'No MX records found'
            return DomainValidationResult(
                domain=domain,
                is_valid=False,
                confidence_penalty=0.1,  # Heavy penalty
                validation_status='no_mx',
                details=details,
                checks_performed=checks_performed
            )
            
        except Exception as e:
            logger.error(f"MX validation failed for {domain}: {e}")
            details['error'] = str(e)
            return DomainValidationResult(
                domain=domain,
                is_valid=False,
                confidence_penalty=0.5,  # Moderate penalty for unknown errors
                validation_status='error',
                details=details,
                checks_performed=checks_performed
            )


class DNSValidator(DomainValidator):
    """Validates domains by checking DNS resolution."""
    
    def validate(self, domain: str) -> DomainValidationResult:
        """Check if domain resolves via DNS."""
        checks_performed = ['dns_resolution']
        details = {}
        
        try:
            # Try to resolve domain to IP
            result = socket.gethostbyname(domain)
            details['resolved_ip'] = result
            
            logger.debug(f"Domain {domain} resolves to {result}")
            return DomainValidationResult(
                domain=domain,
                is_valid=True,
                confidence_penalty=1.0,  # No penalty
                validation_status='valid',
                details=details,
                checks_performed=checks_performed
            )
            
        except socket.gaierror as e:
            logger.warning(f"Domain {domain} DNS resolution failed: {e}")
            details['error'] = str(e)
            return DomainValidationResult(
                domain=domain,
                is_valid=False,
                confidence_penalty=0.2,  # Significant penalty
                validation_status='no_dns',
                details=details,
                checks_performed=checks_performed
            )
            
        except Exception as e:
            logger.error(f"DNS validation failed for {domain}: {e}")
            details['error'] = str(e)
            return DomainValidationResult(
                domain=domain,
                is_valid=False,
                confidence_penalty=0.5,  # Moderate penalty
                validation_status='error',
                details=details,
                checks_performed=checks_performed
            )


class FormatValidator(DomainValidator):
    """Validates domain format and patterns."""
    
    def validate(self, domain: str) -> DomainValidationResult:
        """Check if domain has valid format."""
        import re
        from ..confidence import SUSPICIOUS_DOMAIN_PATTERNS
        
        checks_performed = ['format_validation']
        details = {}
        
        # Basic format validation
        if not domain or len(domain) < 3:
            details['error'] = 'Domain too short'
            return DomainValidationResult(
                domain=domain,
                is_valid=False,
                confidence_penalty=0.0,
                validation_status='invalid_format',
                details=details,
                checks_performed=checks_performed
            )
        
        # Check against suspicious patterns
        for pattern in SUSPICIOUS_DOMAIN_PATTERNS:
            if re.match(pattern, domain, re.IGNORECASE):
                details['suspicious_pattern'] = pattern
                logger.warning(f"Domain {domain} matches suspicious pattern: {pattern}")
                return DomainValidationResult(
                    domain=domain,
                    is_valid=False,
                    confidence_penalty=0.1,
                    validation_status='invalid_format',
                    details=details,
                    checks_performed=checks_performed
                )
        
        # RFC-compliant domain format validation
        domain_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$"
        if not re.match(domain_pattern, domain):
            details['error'] = 'Invalid domain format'
            return DomainValidationResult(
                domain=domain,
                is_valid=False,
                confidence_penalty=0.0,
                validation_status='invalid_format',
                details=details,
                checks_performed=checks_performed
            )
        
        return DomainValidationResult(
            domain=domain,
            is_valid=True,
            confidence_penalty=1.0,
            validation_status='valid',
            details=details,
            checks_performed=checks_performed
        )


class ComprehensiveDomainValidator:
    """
    Comprehensive domain validation service that runs multiple validators.
    
    This is the main service that orchestrates all domain validation checks
    and provides a consolidated result with confidence adjustments.
    """
    
    def __init__(self, skip_network_checks: bool = False):
        """
        Initialize the comprehensive validator.
        
        Args:
            skip_network_checks: If True, skip MX and DNS checks (useful for testing)
        """
        self.validators = [FormatValidator()]
        
        if not skip_network_checks:
            self.validators.extend([
                MXRecordValidator(),
                DNSValidator()
            ])
    
    def validate_domain(self, domain: str) -> DomainValidationResult:
        """
        Run comprehensive domain validation.
        
        Returns the most restrictive result from all validators.
        MX record validation is weighted most heavily.
        """
        if not domain:
            return DomainValidationResult(
                domain="",
                is_valid=False,
                confidence_penalty=0.0,
                validation_status='invalid_format',
                details={'error': 'Empty domain'},
                checks_performed=[]
            )
        
        all_results = []
        combined_details = {}
        all_checks = []
        
        # Run all validators
        for validator in self.validators:
            try:
                result = validator.validate(domain)
                all_results.append(result)
                all_checks.extend(result.checks_performed)
                
                # Merge details
                validator_name = validator.__class__.__name__
                combined_details[validator_name] = {
                    'status': result.validation_status,
                    'penalty': result.confidence_penalty,
                    'details': result.details
                }
                
            except Exception as e:
                logger.error(f"Validator {validator.__class__.__name__} failed for {domain}: {e}")
                combined_details[validator.__class__.__name__] = {
                    'status': 'error',
                    'penalty': 0.5,
                    'details': {'error': str(e)}
                }
        
        # Determine overall result
        # Domain is valid only if ALL validators pass
        is_valid = all(result.is_valid for result in all_results)
        
        # Calculate confidence penalty (use the most restrictive)
        confidence_penalty = min(result.confidence_penalty for result in all_results) if all_results else 0.0
        
        # Determine overall status
        if not is_valid:
            # Prioritize specific error types
            for result in all_results:
                if result.validation_status == 'no_mx':
                    validation_status = 'no_mx'
                    break
                elif result.validation_status == 'no_dns':
                    validation_status = 'no_dns'
                    break
                elif result.validation_status == 'invalid_format':
                    validation_status = 'invalid_format'
                    break
            else:
                validation_status = 'error'
        else:
            validation_status = 'valid'
        
        return DomainValidationResult(
            domain=domain,
            is_valid=is_valid,
            confidence_penalty=confidence_penalty,
            validation_status=validation_status,
            details=combined_details,
            checks_performed=list(set(all_checks))
        )
    
    def validate_and_adjust_confidence(self, domain: str, original_confidence: float) -> Dict[str, Any]:
        """
        Validate domain and return adjusted confidence with details.
        
        Args:
            domain: Domain to validate
            original_confidence: Original confidence score (0.0-1.0)
            
        Returns:
            Dict with validation results and adjusted confidence
        """
        validation_result = self.validate_domain(domain)
        adjusted_confidence = original_confidence * validation_result.confidence_penalty
        
        return {
            'domain': domain,
            'original_confidence': original_confidence,
            'adjusted_confidence': min(adjusted_confidence, 1.0),
            'validation_result': validation_result,
            'confidence_penalty': validation_result.confidence_penalty,
            'is_valid': validation_result.is_valid,
            'validation_status': validation_result.validation_status
        }
