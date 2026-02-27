---
name: apollo-enrichment
description: "B2B lead enrichment and sales intelligence using Apollo.io. Enrich contact data, find prospects, and access 210M+ contacts and 35M+ companies for sales automation workflows."
homepage: https://apollo.io
metadata:
  openclaw:
    emoji: 🎯
    requires:
      env:
        - APOLLO_API_KEY
      bins:
        - python3
      anyBins:
        - pip
        - pip3
    primaryEnv: APOLLO_API_KEY
    install:
      - type: brew
        pkg: python@3.11
      - type: pip
        pkg: requests
---

# Apollo.io Lead Enrichment

B2B sales intelligence and lead enrichment powered by Apollo.io's database of 210+ million contacts and 35+ million companies. Perfect for enriching leads from forms, emails, and CRM systems.

## When to Use

✅ **USE this skill when:**
- Enriching lead data from email or form submissions
- Finding contact information for B2B prospects
- Appending company data to partial lead records
- Building targeted prospect lists
- Verifying and completing incomplete CRM data

❌ **DON'T use when:**
- B2C consumer data (not Apollo's focus)
- Real-time email validation only (use ZeroBounce)
- Social media scraping (use dedicated tools)
- GDPR-sensitive personal data enrichment

## Quick Start

### 1. Get API Key

```bash
# Sign up at https://apollo.io (free tier: 50 credits/month)
# Store in OpenClaw:
openclaw configure --section skills --set apollo.apiKey=your_api_key_here
```

### 2. Enrich a Person

```python
from apollo_client import ApolloClient

client = ApolloClient()

# Enrich with email
result = client.enrich_person(
    email="john.doe@company.com"
)

print(f"Name: {result.get('first_name')} {result.get('last_name')}")
print(f"Title: {result.get('title')}")
print(f"Company: {result.get('organization', {}).get('name')}")
```

### 3. Search for Prospects

```python
# Find prospects by criteria
results = client.search_people(
    titles=["CEO", "CTO"],
    company_name="OpenAI",
    limit=10
)

for person in results.get('people', []):
    print(f"{person['name']} - {person['title']}")
```

## API Reference

### `ApolloClient.enrich_person(**params)`

Enrich a single person's data using available identifiers.

| Parameter | Type | Description |
|-----------|------|-------------|
| `email` | str | Professional email address |
| `first_name` | str | First name |
| `last_name` | str | Last name |
| `name` | str | Full name |
| `organization_name` | str | Company name |
| `domain` | str | Company domain |
| `linkedin_url` | str | LinkedIn profile URL |

**Returns:** Dict with enriched person data including:
- `first_name`, `last_name`, `title`
- `email` (verified professional email)
- `organization` (company details)
- `phone_numbers` (if available)
- `linkedin_url`, `twitter_url`

### `ApolloClient.search_people(**filters)`

Search Apollo's database for prospects.

| Parameter | Type | Description |
|-----------|------|-------------|
| `titles` | list | Job titles to match |
| `company_name` | str | Company name |
| `company_domains` | list | Company domains |
| `locations` | list | Geographic locations |
| `industries` | list | Industry categories |
| `limit` | int | Max results (default: 10, max: 100) |

### `ApolloClient.enrich_organization(domain=None, name=None)`

Enrich company/organization data.

| Parameter | Type | Description |
|-----------|------|-------------|
| `domain` | str | Company website domain |
| `name` | str | Company name |

## Use Cases

### Lead Form Enrichment

```python
# Auto-enrich leads from website forms
def process_lead_form(form_data):
    client = ApolloClient()
    
    # Try to enrich with just email
    enrichment = client.enrich_person(email=form_data['email'])
    
    if enrichment.get('status') == 'success':
        return {
            'email': form_data['email'],
            'first_name': enrichment.get('first_name', form_data.get('first_name')),
            'last_name': enrichment.get('last_name', form_data.get('last_name')),
            'company': enrichment.get('organization', {}).get('name'),
            'title': enrichment.get('title'),
            'company_size': enrichment.get('organization', {}).get('estimated_num_employees'),
            'industry': enrichment.get('organization', {}).get('industry'),
            'linkedin': enrichment.get('linkedin_url'),
            'enriched': True
        }
    
    return {**form_data, 'enriched': False}
```

### CRM Data Hygiene

```python
# Clean up incomplete CRM records
def enrich_crm_records(crm_records):
    client = ApolloClient()
    enriched_count = 0
    
    for record in crm_records:
        if not record.get('company') or not record.get('title'):
            result = client.enrich_person(
                email=record['email'],
                first_name=record.get('first_name'),
                last_name=record.get('last_name')
            )
            
            if result.get('status') == 'success':
                record['company'] = record.get('company') or result.get('organization', {}).get('name')
                record['title'] = record.get('title') or result.get('title')
                record['industry'] = result.get('organization', {}).get('industry')
                enriched_count += 1
    
    return crm_records, enriched_count
```

### Prospect List Building

```python
# Build targeted prospect lists
def build_prospect_list(ideal_customer_profile):
    client = ApolloClient()
    
    prospects = client.search_people(
        titles=ideal_customer_profile['titles'],
        company_domains=ideal_customer_profile['target_domains'],
        locations=ideal_customer_profile['locations'],
        limit=100
    )
    
    qualified_prospects = []
    for person in prospects.get('people', []):
        org = person.get('organization', {})
        
        # Filter by company size
        employees = org.get('estimated_num_employees', 0)
        if ideal_customer_profile['min_employees'] <= employees <= ideal_customer_profile['max_employees']:
            qualified_prospects.append({
                'name': f"{person['first_name']} {person['last_name']}",
                'title': person['title'],
                'email': person.get('email'),
                'company': org.get('name'),
                'company_size': employees,
                'linkedin': person.get('linkedin_url')
            })
    
    return qualified_prospects
```

### Email Signature Parsing

```python
# Extract and enrich contacts from email signatures
def process_email_signature(email_text, sender_email):
    client = ApolloClient()
    
    # Extract signature using regex/AI
    signature = extract_signature(email_text)
    
    # Enrich the sender
    enrichment = client.enrich_person(email=sender_email)
    
    if enrichment.get('status') == 'success':
        return {
            'contact': {
                'email': sender_email,
                'name': f"{enrichment.get('first_name')} {enrichment.get('last_name')}",
                'title': enrichment.get('title'),
                'company': enrichment.get('organization', {}).get('name'),
                'phone': enrichment.get('phone_numbers', [{}])[0].get('sanitized_number')
            },
            'confidence': 'high' if enrichment.get('email') else 'medium'
        }
```

### Competitor Employee Tracking

```python
# Monitor key personnel at competitor companies
def track_competitor_personnel(competitor_domains):
    client = ApolloClient()
    
    key_personnel = {}
    for domain in competitor_domains:
        # Search for executives
        executives = client.search_people(
            company_domains=[domain],
            titles=["CEO", "CTO", "VP", "Director", "Head"],
            limit=20
        )
        
        key_personnel[domain] = [
            {
                'name': f"{p['first_name']} {p['last_name']}",
                'title': p['title'],
                'linkedin': p.get('linkedin_url')
            }
            for p in executives.get('people', [])
        ]
    
    return key_personnel
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ApolloAuthError` | Invalid API key | Check APOLLO_API_KEY |
| `ApolloRateLimitError` | Credit limit exceeded | Wait for reset or upgrade plan |
| `ApolloNotFoundError` | Person not in database | Try with more/less identifiers |
| `ApolloValidationError` | Invalid parameters | Check API docs for correct format |

## Pricing

- **Free**: 50 credits/month (API access)
- **Basic**: $59/month - 1,000 credits
- **Professional**: $99/month - 3,000 credits
- **Organization**: Custom pricing

**Credit Usage:**
- Person enrichment: 1 credit
- Organization enrichment: 1 credit
- Person search: 1 credit per page

## Integration Examples

### With Calendly → HubSpot Flow

```python
# Enrich Calendly bookings before creating HubSpot contacts
def process_calendly_booking(event_data):
    apollo = ApolloClient()
    
    # Enrich the attendee
    enriched = apollo.enrich_person(email=event_data['invitee_email'])
    
    if enriched.get('status') == 'success':
        # Create enriched HubSpot contact
        hubspot_contact = {
            'email': event_data['invitee_email'],
            'firstname': enriched.get('first_name'),
            'lastname': enriched.get('last_name'),
            'jobtitle': enriched.get('title'),
            'company': enriched.get('organization', {}).get('name'),
            'industry': enriched.get('organization', {}).get('industry'),
            'num_employees': enriched.get('organization', {}).get('estimated_num_employees'),
            'linkedin': enriched.get('linkedin_url'),
            'source': 'Calendly Meeting',
            'meeting_date': event_data['start_time']
        }
        
        create_hubspot_contact(hubspot_contact)
```

### With Email Automation

```python
# Enrich email senders for better context
def enrich_incoming_email(email_data):
    apollo = ApolloClient()
    
    # Enrich sender
    sender_info = apollo.enrich_person(email=email_data['from'])
    
    # Add context to email
    email_data['sender_context'] = {
        'title': sender_info.get('title'),
        'company': sender_info.get('organization', {}).get('name'),
        'company_size': sender_info.get('organization', {}).get('estimated_num_employees'),
        'linkedin': sender_info.get('linkedin_url'),
        'priority_score': calculate_priority(sender_info)
    }
    
    return email_data
```

## CLI Usage

```bash
# Enrich a single email
python apollo_client.py enrich --email john@company.com

# Search for prospects
python apollo_client.py search --titles "CEO" --company "OpenAI"

# Enrich from CSV
python apollo_client.py batch --input leads.csv --output enriched_leads.csv
```

## Rate Limits

- **Free tier**: 50 requests/minute
- **Paid tiers**: 200 requests/minute
- Implements automatic retry with exponential backoff

---

**Last Updated:** 2026-02-26 | **Status:** Production Ready v1.0
