import json
import re
import logging
from typing import Dict, Any
from ..models.cache import Company, Employee
from ..agents import get_agent
from ..prompts import (
    COMPANY_EMAIL_DOMAIN_PROMPT_V2,
    EMPLOYEE_EMAIL_PROMPT_V2,
)
from .cache import (
    get_company_from_cache,
    get_employee_from_cache,
    save_company_to_cache,
    save_employee_to_cache,
)

logger = logging.getLogger(__name__)


DEFAULT_AGENT = "gemini"
COMPANY_PROMPT_VERSION = COMPANY_EMAIL_DOMAIN_PROMPT_V2
EMPLOYEE_PROMPT_VERSION = EMPLOYEE_EMAIL_PROMPT_V2


def extract_json_from_llm_response(text: str) -> str:
    """Extract the complete JSON object from a string, handling nested objects properly."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*", "", text)
        text = text.strip("`\n")

    # Find the start of JSON
    start_idx = text.find("{")
    if start_idx == -1:
        return text

    # Count braces to find the complete JSON object
    brace_count = 0
    for i, char in enumerate(text[start_idx:], start_idx):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return text[start_idx : i + 1]

    # If we didn't find a complete JSON, return the original text
    return text


def find_or_create_company(
    company_query: str, use_cache: bool = True, agent_name: str = None
) -> tuple[Company, bool]:
    """
    Find company in cache or create new one using LLM.

    Returns:
        tuple: (Company object, cache_hit: bool)
    """
    # Try to find existing company only if use_cache is True
    if use_cache:
        company = get_company_from_cache(company_query)
        if company:
            return company, True

    # Get the configured agent function
    agent_func = get_agent(agent_name or DEFAULT_AGENT)

    # Use the configured prompt template
    prompt = COMPANY_PROMPT_VERSION.format(company_query=company_query)

    try:
        llm_response = agent_func(prompt)
        logger.info(
            f"[{agent_name or DEFAULT_AGENT}] Company response for '{company_query}': {llm_response}"
        )
        data = json.loads(extract_json_from_llm_response(llm_response))

        # Create or update company
        company = save_company_to_cache(
            name=data.get("name", company_query),
            primary_domain=data.get(
                "primary_domain", f"{company_query.lower().replace(' ', '')}.com"
            ),
            email_patterns=data.get("email_patterns", []),
            known_emails=data.get("known_emails", []),
            all_domains=data.get("all_domains", []),
            summary=data.get("summary", ""),
        )

        return company, False

    except Exception as e:
        logger.error(f"[{agent_name or DEFAULT_AGENT}] Company search failed: {e}")
        # Fallback: create minimal company record
        company = save_company_to_cache(
            name=company_query,
            primary_domain=f"{company_query.lower().replace(' ', '')}.com",
            email_patterns=[
                {"pattern": "first.last", "confidence": 0.5, "source": "fallback"}
            ],
            summary="",
        )
        return company, False


def find_or_create_employee(
    company: Company, person_name: str, use_cache: bool = True, agent_name: str = None
) -> tuple[Employee, bool]:
    """
    Find employee in cache or create new one using LLM.

    Returns:
        tuple: (Employee object, cache_hit: bool)
    """
    # Try to find existing employee only if use_cache is True
    if use_cache:
        employee = get_employee_from_cache(company, person_name)
        if employee:
            return employee, True

    # Get the configured agent function
    agent_func = get_agent(agent_name or DEFAULT_AGENT)

    # Use the configured prompt template
    prompt = EMPLOYEE_PROMPT_VERSION.format(
        person_name=person_name,
        company_name=company.name,
        primary_domain=company.primary_domain,
        email_patterns=company.email_patterns,
        known_emails=company.known_emails,
    )

    try:
        llm_response = agent_func(prompt)
        logger.info(
            f"[{agent_name or DEFAULT_AGENT}] Employee response for '{person_name}' at '{company.name}': {llm_response}"
        )

        json_str = extract_json_from_llm_response(llm_response)
        data = json.loads(json_str)

        # Create or update employee
        employee = save_employee_to_cache(
            company=company,
            full_name=person_name,
            primary_email=data.get("primary_email", ""),
            name_variations=data.get("name_variations", {}),
            candidate_emails=data.get("candidate_emails", []),
            additional_info=data.get("additional_info", {}),
        )

        return employee, False

    except Exception as e:
        logger.error(f"[{agent_name or DEFAULT_AGENT}] Employee search failed: {e}")
        # Fallback: create minimal employee record
        employee = save_employee_to_cache(
            company=company,
            full_name=person_name,
            primary_email="",
            candidate_emails=[],
            additional_info={},
        )
        return employee, False


def find_contact(
    company_query: str, person_name: str, use_cache: bool = True
) -> Dict[str, Any]:
    """
    Simplified contact finder without LangGraph.

    Args:
        company_query: Company name or identifier
        person_name: Full name of the person
        use_cache: If False, bypass cache and use fresh LLM lookup

    Returns:
        Dict with email, confidence, and reasoning
    """
    reasoning_trail = []

    # Step 1: Find or create company
    company, company_cache_hit = find_or_create_company(company_query, use_cache)
    reasoning_trail.append(
        f"Company lookup: {'cache hit' if company_cache_hit else 'fresh search'} for '{company_query}'"
    )

    # Step 3: Find or create employee
    employee, employee_cache_hit = find_or_create_employee(
        company, person_name, use_cache
    )
    reasoning_trail.append(
        f"Employee lookup: {'cache hit' if employee_cache_hit else 'fresh search'} for '{person_name}'"
    )

    # Step 4: Prepare response
    candidate_emails = employee.candidate_emails or []
    if candidate_emails:
        # Sort by final_score descending and take the best one
        best_candidate = max(candidate_emails, key=lambda x: x.get("final_score", 0))
        email = best_candidate["email"]
        confidence = best_candidate["final_score"]
        pattern_used = best_candidate.get("source")
        alternatives = [c["email"] for c in candidate_emails if c["email"] != email][:3]
    else:
        # Fallback to primary_email
        email = employee.primary_email or None
        confidence = 0.0
        pattern_used = None
        alternatives = []

    # Determine cache hit status
    if company_cache_hit and employee_cache_hit:
        cache_hit = "both"
    elif company_cache_hit:
        cache_hit = "company"
    elif employee_cache_hit:
        cache_hit = "employee"
    else:
        cache_hit = "none"

    return {
        # Employee data
        "email": email,
        "confidence": confidence,
        "candidate_emails": candidate_emails,
        "additional_info": employee.additional_info,
        # Company data
        "company_name": company.name,
        "company_summary": company.summary,
        "primary_domain": company.primary_domain,
        "email_patterns": company.email_patterns,
        "all_domains": company.all_domains,
        "known_emails": company.known_emails,
        # Process metadata
        "pattern_used": pattern_used,
        "alternatives": alternatives,
        "reasoning": " | ".join(reasoning_trail),
        "cache_hit": cache_hit,
    }
