#!/usr/bin/env python
"""
Quick test script to debug LLM responses
"""
import os
import sys
import django
import traceback

# Add the project root to Python path
sys.path.insert(0, 'd:/Codes/Work/SSS/contact-finder')

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from contactfinder.services import find_contact

def test_llm():
    print("Script started...")
    try:
        print("About to import...")
        from contactfinder.services import find_contact
        print("Import successful!")
        
        print("Starting LLM test...")
        
        # Test the service directly
        result = find_contact(
            company_query="Humana Apparels",
            person_name="Hojayfa Rahman", 
            use_cache=False  # Force fresh lookup
        )

        print("=== Result ===")
        for key, value in result.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_llm()
