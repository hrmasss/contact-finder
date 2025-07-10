# Company research prompts
COMPANY_EMAIL_DOMAIN_PROMPT_V1 = """
You are a company research assistant specializing in finding email domains and patterns.

Task: Find the PRIMARY EMAIL DOMAIN for "{company_query}"

CRITICAL: The website domain and email domain are often different. Focus on actual email addresses, not just website URLs.

COMPREHENSIVE DOMAIN SEARCH STRATEGY:
1. Scrape ALL available domains associated with the company from the web
2. Look for actual email addresses in: Contact pages, press releases, job postings, official directories, LinkedIn, news articles, SEC filings, patents
3. Count email occurrences per domain to identify the most used one
4. Choose the domain that has the MOST public emails AND is relevant to the company (matches company name or parent company name)
5. If part of a parent company, check parent company email patterns
6. Verify domain relevance - does it correspond to the company name or parent company?

Return ONLY valid JSON:
{{
    "name": "Official Company Name",
    "summary": "Brief 2-3 sentence summary of what the company does and its industry",
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

ENHANCED DOMAIN DISCOVERY PROTOCOL:
1. COMPREHENSIVE SCRAPING: Search ALL available domains associated with the company across the web
2. EMAIL HUNTING: Look for actual email addresses in: Contact pages, press releases, WHOIS data, LinkedIn job posts, news articles, SEC filings, patents, conference listings, company directories
3. DOMAIN ANALYSIS: Count email occurrences per domain - the domain with the MOST public emails wins
4. RELEVANCE CHECK: Ensure chosen domain corresponds to company name or parent company name
5. SUBSIDIARY INVESTIGATION: Check if company is subsidiary - parent companies often control email domains
6. PATTERN EXTRACTION: Analyze email patterns from all found addresses

ONLY return JSON with actual findings:
{{
    "name": "Exact Company Name Found",
    "summary": "Brief 2-3 sentence summary of what the company does and its industry",
    "primary_domain": "real-email-domain.com",
    "email_patterns": [
        {{"pattern": "first.last", "confidence": 0.95, "source": "found_in_news_articles"}},
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

PRIORITY SEARCH STRATEGY:
1. PUBLIC SEARCH FIRST: Search for direct mention of this person's email in public sources (LinkedIn, company directory, news, press releases, conference listings)
2. If found in public sources, use that email - NO NEED to rely on patterns
3. If NOT found publicly, then apply company patterns to generate candidates
4. Consider name variations (nicknames, initials, cultural naming)
5. Rank by likelihood based on company patterns and public information

Return ONLY JSON matching this exact schema:
{{
    "primary_email": "best.guess@domain.com",
    "name_variations": {{
        "first_name": "FirstName",
        "last_name": "LastName",
        "nickname": "Nick",
        "initials": "FN"
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
            "email": "firstname.lastname@domain.com",
            "confidence": 0.9,
            "source": "public_found_or_pattern_match",
            "reasoning": "Found in LinkedIn profile or Matches primary company pattern",
            "final_score": 0.85
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

ENHANCED SEARCH PROTOCOL:
1. PUBLIC SEARCH PRIORITY: First search extensively for this person's info in public sources (LinkedIn, company directory, news mentions, press releases, conference speaker lists, research papers, patents)
2. IF FOUND IN PUBLIC: Use that email directly - pattern matching becomes unnecessary
3. IF NOT FOUND: Generate candidates using proven company patterns
4. COMPREHENSIVE INFO GATHERING: Collect additional info about the person (title, role, location, etc.)
5. NAME PROCESSING: Account for name complexities (middle names, cultural variations, preferred names)

Output requirements - ONLY JSON matching exact schema:
{{
    "primary_email": "best.candidate@domain.com",
    "name_variations": {{
        "first_name": "Primary",
        "last_name": "Surname", 
        "nickname": "PreferredName",
        "initials": "P.S."
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
            "source": "public_found_or_company_pattern_applied",
            "reasoning": "Found in LinkedIn profile or first.last pattern with 90% company usage",
            "final_score": 0.81
        }}
    ]
}}
"""

COMPANY_EMAIL_DOMAIN_PROMPT_V3 = """
You are an expert email domain investigator. Your job is to determine the **actual email domain used by employees of** "{company_query}".

IMPORTANT: A company’s website domain (e.g., www.company.com) is **not always the same** as their email domain (e.g., @corp-mail.com). Focus only on domains **actually used in real email addresses**.

YOUR GOAL:

1. Find real email addresses used by the company (e.g., from their contact pages, press releases, staff directories, job listings, conference materials, LinkedIn, etc.)
2. Identify the **primary domain** — the one used most consistently for employee or official contact emails.
3. Detect the common email naming patterns (e.g., first.last@domain.com)
4. If the company is part of a larger group, list any parent company domains or shared patterns.
5. Output must follow this JSON format:

{{
  "name": "Full Official Company Name",
  "summary": "1-2 sentence summary of what the company does",
  "primary_domain": "actualemaildomain.com",
  "email_patterns": [
    {{"pattern": "first.last", "confidence": 0.95, "source": "press_release"}},
    {{"pattern": "f.lastname", "confidence": 0.7, "source": "employee directory"}}
  ],
  "known_emails": [
    {{"email": "contact@actualemaildomain.com", "source": "contact page"}},
    {{"email": "john.doe@actualemaildomain.com", "source": "press release"}}
  ],
  "all_domains": [
    {{"domain": "actualemaildomain.com", "type": "primary", "confidence": 0.95}},
    {{"domain": "groupcorp.com", "type": "parent", "confidence": 0.7}}
  ]
}}

CRITICAL NOTES:
- Do NOT assume the website domain is used for email unless confirmed by real email addresses.
- Use structured sources only (no hallucination).
"""


EMPLOYEE_EMAIL_PROMPT_V3 = """
You are an expert in email pattern inference.

Your task is to **find or guess the most likely email address** for this person:

- Full Name: "{person_name}"
- Company: "{company_name}"
- Primary Email Domain: "{primary_domain}" (from company analysis)
- Known Patterns: {email_patterns} (from email domain analysis)
- Real examples: {known_emails}

STEP-BY-STEP:

1. Search publicly available information (conferences, staff listings, academic papers, blogs, press, LinkedIn) for a **direct email** for the person. If found, return it immediately with the source.

2. If no public email is found, **use the company’s domain and naming patterns** to make a best-guess.

3. If the person has a personal website, GitHub, LinkedIn, or university profile, consider those for alternative addresses too.

4. Return a JSON object with the following fields:

{{
    "primary_email": "best.candidate@domain.com",
    "name_variations": {{
        "first_name": "Primary",
        "last_name": "Surname", 
        "nickname": "PreferredName",
        "initials": "P.S."
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
            "source": "public_found_or_company_pattern_applied",
            "reasoning": "Found in LinkedIn profile or first.last pattern with 90% company usage",
            "final_score": 0.81
        }}
    ]
}}

RULES:
- Never guess if a valid public address is already found.
- Always use naming patterns backed by evidence from the company domain prompt.
- If the domain is part of a parent company, consider parent domains and patterns too.
"""
