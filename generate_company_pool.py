import json
from faker import Faker

NUM_COMPANIES = 100
OUTPUT_FILE = 'data/company_pool.json'

fake = Faker()

company_pool = []
for i in range(NUM_COMPANIES):
    company_id = 10000 + i
    company_name = fake.company()
    company_pool.append({
        'company_id': company_id,
        'company_name': company_name
    })

with open(OUTPUT_FILE, 'w') as f:
    json.dump(company_pool, f, indent=2)

print(f"Generated {NUM_COMPANIES} companies in {OUTPUT_FILE}")
