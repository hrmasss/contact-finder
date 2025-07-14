DOMAIN_DISCOVERY_PROMPT = """
You are an expert at finding company domain information. Given a company name and optional additional context, find the company's email domains and basic information.

Company Query: {company_query}
Additional Context: {additional_info}

Your task:
1. Find the company's email domains (domains used for employee emails)
2. Gather basic company metadata (website, summary, location, industry, etc.)
3. Identify potential search aliases (alternative names for this company)
4. Provide confidence scores for each domain based on evidence quality

Search for publicly available information about this company including:
- Official website and contact information
- Press releases and news articles
- Directory listings and social media profiles
- Any public email addresses to confirm domains

Return your findings in this JSON format:
{{
    "companies": [
        {{
            "name": "Company Name",
            "email_domains": [
                {{
                    "domain": "company.com",
                    "confidence": 0.95,
                    "source": "official_website"
                }},
                {{
                    "domain": "mail.company.com",
                    "confidence": 0.8,
                    "source": "mx_records"
                }}
            ],
            "metadata": {{
                "website": "https://company.com",
                "summary": "Brief company description",
                "location": "San Francisco, CA",
                "industry": "Technology",
                "linkedin": "https://linkedin.com/company/company",
                "employee_count": "1000-5000",
                "founded": "2010"
            }},
            "search_aliases": ["Company Inc", "Company Corp", "COMPANY"]
        }}
    ]
}}

Focus on accuracy and provide realistic confidence scores (0.0-1.0) based on evidence quality.

IMPORTANT: Return ONLY valid JSON in your response. Do not include any explanatory text, markdown formatting, or additional commentary.
"""

PATTERN_DISCOVERY_PROMPT = """
You are an expert at analyzing email patterns for companies. Given a domain, find common email patterns and known public emails.

Domain: {domain}

Your task:
1. Search for publicly available email addresses from this domain
2. Analyze patterns (e.g., first.last@domain.com, firstlast@domain.com, f.last@domain.com)
3. Determine pattern confidence based on evidence
4. Find known public emails for validation

Search for:
- Contact pages and employee directories
- Press releases with contact information
- Social media profiles and news articles
- Any public email addresses from this domain

Return your findings in this JSON format:
{{
    "patterns": [
        {{
            "domain": "{domain}",
            "pattern": "first.last",
            "confidence": 0.9,
            "source": "found_examples",
            "verified_count": 5
        }},
        {{
            "domain": "{domain}",
            "pattern": "firstlast",
            "confidence": 0.7,
            "source": "inferred",
            "verified_count": 2
        }}
    ],
    "known_emails": [
        {{
            "email": "john.doe@{domain}",
            "source": "company_website",
            "confidence": 0.9
        }},
        {{
            "email": "info@{domain}",
            "source": "contact_page",
            "confidence": 0.95
        }}
    ]
}}

Common patterns to look for:
- first.last@domain.com
- firstlast@domain.com  
- f.last@domain.com
- first.l@domain.com
- first_last@domain.com
- last.first@domain.com

Provide realistic confidence scores (0.0-1.0) based on evidence quality and verified count.

IMPORTANT: Return ONLY valid JSON in your response. Do not include any explanatory text, markdown formatting, or additional commentary.
"""
