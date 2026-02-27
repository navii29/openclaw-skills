#!/usr/bin/env python3
"""
Apollo.io Enrichment - Usage Examples

Practical examples for common B2B lead enrichment workflows.
"""

import os
import json
from apollo_client import ApolloClient, ApolloAuthError


def example_1_basic_enrichment():
    """Basic person enrichment with email"""
    print("=" * 60)
    print("Example 1: Basic Email Enrichment")
    print("=" * 60)
    
    client = ApolloClient()
    
    # Enrich with just an email
    result = client.enrich_person(
        email="john.doe@company.com"
    )
    
    if result['status'] == 'success':
        person = result['data']
        print(f"✅ Found: {person.get('first_name')} {person.get('last_name')}")
        print(f"   Title: {person.get('title')}")
        
        org = person.get('organization', {})
        print(f"   Company: {org.get('name')}")
        print(f"   Industry: {org.get('industry')}")
        print(f"   Employees: {org.get('estimated_num_employees')}")
    else:
        print(f"❌ {result.get('message', 'Not found')}")
    
    print()


def example_2_partial_data_enrichment():
    """Enrich with partial data (name + company)"""
    print("=" * 60)
    print("Example 2: Enrich with Partial Data")
    print("=" * 60)
    
    client = ApolloClient()
    
    # You only have name and company
    result = client.enrich_person(
        first_name="Elon",
        last_name="Musk",
        organization_name="Tesla"
    )
    
    if result['status'] == 'success':
        person = result['data']
        print(f"✅ Found: {person.get('first_name')} {person.get('last_name')}")
        print(f"   LinkedIn: {person.get('linkedin_url')}")
        print(f"   Email: {person.get('email', 'Not available')}")
    else:
        print(f"❌ Could not enrich with provided data")
    
    print()


def example_3_organization_enrichment():
    """Enrich company/organization data"""
    print("=" * 60)
    print("Example 3: Organization Enrichment")
    print("=" * 60)
    
    client = ApolloClient()
    
    result = client.enrich_organization(
        domain="stripe.com"
    )
    
    if result['status'] == 'success':
        org = result['data']
        print(f"✅ Company: {org.get('name')}")
        print(f"   Website: {org.get('website_url')}")
        print(f"   Employees: {org.get('estimated_num_employees')}")
        print(f"   Industry: {org.get('industry')}")
        print(f"   Location: {org.get('location', {}).get('address')}")
        
        # List technologies used
        techs = org.get('technographics', [])
        if techs:
            print(f"   Technologies: {', '.join([t['name'] for t in techs[:5]])}")
    else:
        print("❌ Organization not found")
    
    print()


def example_4_prospect_search():
    """Search for prospects by criteria"""
    print("=" * 60)
    print("Example 4: Prospect Search")
    print("=" * 60)
    
    client = ApolloClient()
    
    # Find CEOs at tech companies
    results = client.search_people(
        titles=["CEO", "Founder"],
        company_domains=["stripe.com", "notion.so"],
        limit=5
    )
    
    print(f"Found {results.get('total_entries', 0)} total results")
    print(f"Showing first {len(results.get('people', []))}:")
    
    for person in results.get('people', []):
        org = person.get('organization', {})
        print(f"  • {person.get('first_name')} {person.get('last_name')}")
        print(f"    {person.get('title')} at {org.get('name')}")
        print(f"    LinkedIn: {person.get('linkedin_url', 'N/A')}")
        print()


def example_5_lead_form_processing():
    """Process and enrich leads from a form submission"""
    print("=" * 60)
    print("Example 5: Lead Form Processing")
    print("=" * 60)
    
    # Simulated form submission
    form_submissions = [
        {"email": "sarah.chen@startup.io", "first_name": "Sarah"},
        {"email": "mike@enterprise.com", "first_name": "Mike", "last_name": "Johnson"},
    ]
    
    client = ApolloClient()
    enriched_leads = []
    
    for lead in form_submissions:
        print(f"Processing: {lead['email']}")
        
        result = client.enrich_person(
            email=lead['email'],
            first_name=lead.get('first_name'),
            last_name=lead.get('last_name')
        )
        
        if result['status'] == 'success':
            person = result['data']
            org = person.get('organization', {})
            
            enriched = {
                'email': lead['email'],
                'first_name': person.get('first_name', lead.get('first_name')),
                'last_name': person.get('last_name', lead.get('last_name')),
                'title': person.get('title'),
                'company': org.get('name'),
                'company_size': org.get('estimated_num_employees'),
                'industry': org.get('industry'),
                'linkedin': person.get('linkedin_url'),
                'enriched': True,
                'lead_score': calculate_lead_score(person, org)
            }
            enriched_leads.append(enriched)
            print(f"  ✅ Enriched: {enriched['first_name']} {enriched['last_name']}")
            print(f"     Company: {enriched['company']} ({enriched['company_size']} employees)")
            print(f"     Lead Score: {enriched['lead_score']}/100")
        else:
            print(f"  ⚠️ Could not enrich, keeping original data")
            enriched_leads.append({**lead, 'enriched': False})
        
        print()
    
    return enriched_leads


def example_6_crm_data_hygiene():
    """Clean up incomplete CRM records"""
    print("=" * 60)
    print("Example 6: CRM Data Hygiene")
    print("=" * 60)
    
    # Simulated incomplete CRM records
    crm_records = [
        {"email": "contact1@techcorp.com", "first_name": "Alex", "company": None},
        {"email": "contact2@startup.io", "first_name": "Jordan", "title": None, "company": None},
    ]
    
    client = ApolloClient()
    
    for record in crm_records:
        print(f"Before: {record}")
        
        if not record.get('company') or not record.get('title'):
            result = client.enrich_person(email=record['email'])
            
            if result['status'] == 'success':
                person = result['data']
                org = person.get('organization', {})
                
                # Fill in missing fields
                record['first_name'] = record.get('first_name') or person.get('first_name')
                record['last_name'] = person.get('last_name')
                record['company'] = record.get('company') or org.get('name')
                record['title'] = record.get('title') or person.get('title')
                record['industry'] = org.get('industry')
                record['data_quality'] = 'enriched'
        
        print(f"After:  {record}")
        print()


def example_7_batch_processing():
    """Process multiple leads in batch"""
    print("=" * 60)
    print("Example 7: Batch Processing")
    print("=" * 60)
    
    people_to_enrich = [
        {"email": "person1@company1.com"},
        {"email": "person2@company2.com"},
        {"first_name": "Jane", "last_name": "Doe", "organization_name": "Acme Inc"},
    ]
    
    client = ApolloClient()
    
    print(f"Enriching {len(people_to_enrich)} people...")
    results = client.bulk_enrich_people(people_to_enrich)
    
    successful = sum(1 for r in results if r['result']['status'] == 'success')
    print(f"✅ Successfully enriched: {successful}/{len(people_to_enrich)}")
    
    for i, result in enumerate(results):
        status = result['result']['status']
        icon = "✅" if status == 'success' else "❌"
        print(f"  {icon} Person {i+1}: {status}")
    
    print()


def calculate_lead_score(person: dict, org: dict) -> int:
    """Calculate a simple lead score based on enrichment data"""
    score = 0
    
    # Title-based scoring
    title = (person.get('title') or '').lower()
    if any(t in title for t in ['ceo', 'cto', 'founder', 'president']):
        score += 40
    elif any(t in title for t in ['vp', 'vice president', 'director', 'head']):
        score += 30
    elif any(t in title for t in ['manager', 'lead']):
        score += 20
    else:
        score += 10
    
    # Company size scoring
    employees = org.get('estimated_num_employees', 0)
    if employees > 1000:
        score += 30
    elif employees > 200:
        score += 20
    elif employees > 50:
        score += 10
    
    # Has LinkedIn
    if person.get('linkedin_url'):
        score += 10
    
    # Has verified email
    if person.get('email'):
        score += 20
    
    return min(score, 100)


def example_8_competitive_intelligence():
    """Monitor key personnel at competitor companies"""
    print("=" * 60)
    print("Example 8: Competitive Intelligence")
    print("=" * 60)
    
    competitor_domains = ["competitor1.com", "competitor2.com"]
    
    client = ApolloClient()
    
    for domain in competitor_domains:
        print(f"\nAnalyzing: {domain}")
        
        # Search for executives
        executives = client.search_people(
            company_domains=[domain],
            titles=["CEO", "CTO", "VP", "Director", "Head"],
            limit=10
        )
        
        key_personnel = []
        for person in executives.get('people', []):
            key_personnel.append({
                'name': f"{person.get('first_name')} {person.get('last_name')}",
                'title': person.get('title'),
                'linkedin': person.get('linkedin_url')
            })
        
        print(f"  Found {len(key_personnel)} key personnel:")
        for p in key_personnel[:5]:  # Show top 5
            print(f"    • {p['name']} - {p['title']}")
    
    print()


def run_all_examples():
    """Run all examples with error handling"""
    examples = [
        example_1_basic_enrichment,
        example_2_partial_data_enrichment,
        example_3_organization_enrichment,
        example_4_prospect_search,
        example_5_lead_form_processing,
        example_6_crm_data_hygiene,
        example_7_batch_processing,
        example_8_competitive_intelligence,
    ]
    
    try:
        # Check for API key
        if not os.getenv('APOLLO_API_KEY'):
            print("⚠️  Warning: APOLLO_API_KEY not set")
            print("   Set it with: export APOLLO_API_KEY=your_key_here")
            print("   Continuing with mock data...\n")
            
            # Mock examples for demonstration
            print("\n" + "=" * 60)
            print("MOCK EXAMPLES (set APOLLO_API_KEY for live data)")
            print("=" * 60 + "\n")
            
            for example in examples:
                try:
                    example()
                except Exception as e:
                    print(f"Error in {example.__name__}: {e}\n")
            return
        
        print("\n" + "=" * 60)
        print("LIVE APOLLO.IO API EXAMPLES")
        print("=" * 60 + "\n")
        
        for example in examples:
            try:
                example()
            except Exception as e:
                print(f"Error in {example.__name__}: {e}\n")
                
    except ApolloAuthError as e:
        print(f"Authentication error: {e}")
        print("Please check your APOLLO_API_KEY")


if __name__ == '__main__':
    run_all_examples()
