# Company research prompts
COMPANY_EMAIL_DOMAIN_PROMPT_V1 = """
You are a company research assistant specializing in finding email domains and patterns.

Task: Find the PRIMARY EMAIL DOMAIN for "{company_query}"

CRITICAL: The website domain and email domain are often different. Focus on actual email addresses, not just website URLs.

Search strategy:
1. Look for "Contact Us" pages, press releases, job postings, and official directories
2. Find actual email addresses used by the company (info@, contact@, careers@, etc.)
3. Identify the domain pattern used for employee emails specifically
4. If part of a parent company, check parent company email patterns

Return ONLY valid JSON:
{{
    "name": "Official Company Name",
    "primary_domain": "actualemail.com",
    "email_patterns": [
        {{"pattern": "first.last", "confidence": 0.9, "source": "verified_emails"}},
        {{"pattern": "firstlast", "confidence": 0.7, "source": "pattern_analysis"}}
    ],
    "known_emails": [
        {{"email": "contact@actualemail.com", "source": "website"}},
        {{"email": "careers@actualemail.com", "source": "job_posting"}}
    ],
    "all_domains": [
        {{"domain": "actualemail.com", "type": "primary", "confidence": 0.95}},
        {{"domain": "parentcompany.com", "type": "parent", "confidence": 0.8}}
    ]
}}
"""

COMPANY_EMAIL_DOMAIN_PROMPT_V2 = """
You are an expert email domain detective. Your job is to find the ACTUAL email domain used by "{company_query}" employees.

WARNING: Website domains ≠ Email domains. Focus on real email addresses only.

Investigation steps:
1. Search for ANY real email addresses from this company
2. Look in: Contact pages, press releases, WHOIS data, LinkedIn job posts, news articles
3. Check if company is subsidiary - parent companies often control email domains
4. Analyze email patterns from found addresses

ONLY return JSON with actual findings:
{{
    "name": "Exact Company Name Found",
    "summary": "Brief 2-3 sentence summary of what the company does and its industry",
    "primary_domain": "real-email-domain.com",
    "confidence_reasoning": "Found 5 employee emails using this domain in press releases",
    "email_patterns": [
        {{"pattern": "f.lastname", "confidence": 0.95, "source": "found_in_news_articles"}},
        {{"pattern": "firstname.l", "confidence": 0.8, "source": "linkedin_posts"}}
    ],
    "known_emails": [
        {{"email": "john.doe@real-email-domain.com", "source": "press_release"}},
        {{"email": "contact@real-email-domain.com", "source": "contact_page"}}
    ],
    "all_domains": [
        {{"domain": "real-email-domain.com", "type": "primary", "confidence": 0.95}},
        {{"domain": "parent.com", "type": "parent", "confidence": 0.8}}
    ]
}}
"""

# Employee search prompts
EMPLOYEE_EMAIL_PROMPT_V1 = """
You are an email discovery specialist. Find the email for "{person_name}" at "{company_name}".

Company email context:
- Primary domain: {primary_domain}
- Known patterns: {email_patterns}
- Sample emails: {known_emails}

Search strategy:
1. Search for direct mention of this person's email in public sources
2. If not found, apply company patterns to generate candidates
3. Consider name variations (nicknames, initials, cultural naming)
4. Rank by likelihood based on company patterns

Return ONLY JSON:
{{
    "primary_email": "best.guess@domain.com",
    "name_variations": {{
        "first_name": "FirstName",
        "last_name": "LastName",
        "nickname": "Nick",
        "initials": "FN"
    }},
    "candidate_emails": [
        {{
            "email": "firstname.lastname@domain.com",
            "confidence": 0.9,
            "source": "pattern_match",
            "reasoning": "Matches primary company pattern",
            "relevance_score": 0.95,
            "final_score": 0.855
        }}
    ]
}}
"""

EMPLOYEE_EMAIL_PROMPT_V2 = """
Find email for: "{person_name}" at "{company_name}"

Available intel:
- Email domain: {primary_domain}
- Confirmed patterns: {email_patterns}  
- Real examples: {known_emails}

Mission: Find their actual email address AND gather additional info

Step 1: Search for direct evidence (LinkedIn, company directory, news mentions)
Step 2: If not found, generate candidates using proven company patterns
Step 3: Account for name complexities (middle names, cultural variations, preferred names)
Step 4: Collect additional info about the person (title, role, location, etc.)

Output requirements - ONLY JSON:
{{
    "primary_email": "best.candidate@domain.com",
    "name_variations": {{
        "first_name": "Primary",
        "last_name": "Surname", 
        "variations": ["nickname", "initial"],
        "cultural_considerations": "Western/Eastern naming conventions"
    }},
    "additional_info": {{
        "title": "Job Title",
        "role": "Role/Position",
        "department": "Department",
        "location": "City, State",
        "linkedin_url": "https://linkedin.com/in/...",
        "bio": "Brief professional summary"
    }},
    "candidate_emails": [
        {{
            "email": "generated@domain.com",
            "confidence": 0.85,
            "source": "company_pattern_applied",
            "reasoning": "first.last pattern with 90% company usage",
            "relevance_score": 0.95,
            "final_score": 0.81
        }}
    ]
}}
"""

# Advanced prompts for better accuracy
EMPLOYEE_EMAIL_PROMPT_V3_ADVANCED = """
MISSION: Locate email for "{person_name}" working at "{company_name}"

CONTEXT:
- Target domain: {primary_domain}
- Verified patterns: {email_patterns}
- Reference emails: {known_emails}

ENHANCED SEARCH PROTOCOL:
1. DIRECT SEARCH: Look for explicit mentions of this person's email
   - Company directories, press releases, LinkedIn posts, conference speakers
   - News articles, patent filings, research papers
   
2. PATTERN ANALYSIS: If no direct hit, analyze company email structure
   - Apply highest-confidence pattern from verified examples
   - Consider position/department-specific variations
   
3. NAME PROCESSING: Handle complex names intelligently
   - Multiple first names: use first or preferred
   - Hyphenated surnames: test both parts and combined
   - International names: consider transliteration
   - Professional vs. legal names
   
4. VALIDATION LOGIC: Score candidates by multiple factors
   - Pattern match strength
   - Name processing accuracy
   - Position appropriateness
   - Domain confidence

REQUIRED OUTPUT (JSON only):
{{
    "analysis": {{
        "direct_search_result": "found/not_found",
        "name_complexity": "simple/moderate/complex",
        "pattern_confidence": 0.95
    }},
    "name_variants": {{
        "first_name": "ProcessedFirst",
        "last_name": "ProcessedLast",
        "preferred_format": "first.last",
        "alternatives": ["f.last", "firstlast"]
    }},
    "top_candidates": [
        {{
            "email": "processed.name@domain.com",
            "confidence": 0.92,
            "reasoning": "Matches highest confidence pattern (85% usage rate)",
            "name_processing": "standard_western",
            "pattern_source": "verified_from_3_examples",
            "final_score": 0.874
        }}
    ],
    "recommended": "best.email@domain.com"
}}
"""
