# 🎯 Apollo.io Lead Enrichment Skill

B2B sales intelligence and lead enrichment for OpenClaw. Powered by Apollo.io's database of 210+ million contacts and 35+ million companies.

## Features

- **Person Enrichment**: Enrich contact data from email, LinkedIn, or partial info
- **Organization Enrichment**: Complete company profiles from domain or name
- **Prospect Search**: Find prospects by title, company, location, industry
- **Batch Processing**: Enrich multiple leads efficiently
- **CRM Integration**: Clean and complete incomplete CRM records

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export APOLLO_API_KEY=your_api_key_here

# Enrich a person
python apollo_client.py enrich --email john@company.com

# Search for prospects
python apollo_client.py search --titles "CEO" --company "OpenAI"

# Run examples
python examples.py

# Run tests
python test_apollo.py
```

## Python Usage

```python
from apollo_client import ApolloClient

client = ApolloClient()

# Enrich by email
result = client.enrich_person(email="john@company.com")

# Search for CEOs at tech companies
results = client.search_people(
    titles=["CEO", "CTO"],
    company_domains=["stripe.com"],
    limit=10
)

# Batch enrichment
people = [
    {"email": "person1@company.com"},
    {"email": "person2@company.com"},
]
results = client.bulk_enrich_people(people)
```

## API Key

Get your free API key at [apollo.io](https://apollo.io) (50 credits/month on free tier).

## Documentation

See [SKILL.md](SKILL.md) for complete documentation.

## License

MIT
