import csv
from properties import prop

def is_duplicate_prop(property_name: str, seen_names: set) -> bool:
    return property_name in seen_names

def is_complete_prop(property: dict, required_keys: list) -> bool:
    return all(key in property for key in required_keys)

def save_prop_to_csv(properties: list, filename: str):
    if not properties:
        print("No properties to save.")
        return

    fieldnames = prop.model_fields.keys()

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(properties)
    print(f"Saved {len(properties)} properties to '{filename}'.")
