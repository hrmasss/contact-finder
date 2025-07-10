from contactfinder.services import find_contact

result = find_contact(
    company_query="Humana Apparels",
    person_name="Hojayfa Rahman", 
    use_cache=False
)

print("=== Final Result ===")
for key, value in result.items():
    print(f"{key}: {value}")
