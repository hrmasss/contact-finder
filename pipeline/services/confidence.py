# Service reliability multipliers
SERVICE_CONFIDENCE_MULTIPLIERS = {
    "rocketreach_api": 0.85,
    "official_website": 0.95,
    "company_website": 0.90,
    "public_documentation": 0.85,
    "gemini_verified": 0.80,
    "gemini_raw": 0.60,
    "linkedin": 0.75,
    "whois": 0.70,
    "social_media": 0.60,
    "inferred": 0.40,
    "fallback": 0.30,
    "unknown": 0.20,
}

# Domain validation patterns
SUSPICIOUS_DOMAIN_PATTERNS = [
    r".*-cloud\.top$",
    r".*temp.*",
    r".*test.*",
    r".*staging.*",
    r".*dev.*",
    r".*fake.*",
    r".*example.*",
    r".*\.tk$",
    r".*\.ml$",
    r".*\.ga$",
    r".*\.cf$",
]

# Email pattern validation
SUSPICIOUS_EMAIL_PATTERNS = [
    "forwarding email domain",
    "temporary email",
    "test email",
    "example email",
    "fake email",
    "noreply@example",
    "dummy@",
]

# Minimum confidence thresholds
MIN_CONFIDENCE_THRESHOLDS = {
    "domain": 0.3,
    "pattern": 0.2,
    "email": 0.3,
}

# Maximum results per service
MAX_RESULTS_PER_SERVICE = {
    "rocketreach": 5,
    "gemini": 3,
    "fallback": 2,
}
