#!/usr/bin/env python3
"""
Apollo.io API Client for B2B Lead Enrichment

Provides integration with Apollo.io's sales intelligence platform for:
- Person/Contact enrichment
- Organization/Company enrichment  
- People search
- Bulk enrichment

API Docs: https://docs.apollo.io/
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

# Handle imports for both module and script usage
try:
    import requests
except ImportError:
    print("Error: requests package required. Install with: pip install requests")
    sys.exit(1)


class ApolloError(Exception):
    """Base exception for Apollo API errors"""
    pass


class ApolloAuthError(ApolloError):
    """Invalid API key or authentication failure"""
    pass


class ApolloRateLimitError(ApolloError):
    """Rate limit or credit quota exceeded"""
    pass


class ApolloNotFoundError(ApolloError):
    """Person or organization not found"""
    pass


class ApolloValidationError(ApolloError):
    """Invalid request parameters"""
    pass


@dataclass
class EnrichmentResult:
    """Standardized enrichment result"""
    status: str
    data: Dict
    credits_used: int
    cached: bool = False


class ApolloClient:
    """
    Apollo.io API Client
    
    Environment:
        APOLLO_API_KEY: Your Apollo.io API key
    
    Usage:
        client = ApolloClient()
        result = client.enrich_person(email="john@company.com")
    """
    
    BASE_URL = "https://api.apollo.io/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Apollo client
        
        Args:
            api_key: Apollo API key (or set APOLLO_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("APOLLO_API_KEY")
        if not self.api_key:
            raise ApolloAuthError(
                "API key required. Set APOLLO_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        })
        
        # Track rate limit info
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 3
    ) -> Dict:
        """
        Make authenticated request to Apollo API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            retry_count: Number of retries for rate limiting
            
        Returns:
            API response as dict
            
        Raises:
            ApolloAuthError: On authentication failure
            ApolloRateLimitError: On rate limit exceeded
            ApolloNotFoundError: On 404 responses
            ApolloValidationError: On validation errors
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        # Add API key to params
        params = params or {}
        params['api_key'] = self.api_key
        
        for attempt in range(retry_count):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=30
                )
                
                # Track rate limits from headers
                self.rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
                self.rate_limit_reset = response.headers.get('X-RateLimit-Reset')
                
                # Handle response codes
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise ApolloAuthError("Invalid API key. Check APOLLO_API_KEY.")
                elif response.status_code == 429:
                    if attempt < retry_count - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        time.sleep(wait_time)
                        continue
                    raise ApolloRateLimitError(
                        "Rate limit exceeded. Wait before retrying or upgrade your plan."
                    )
                elif response.status_code == 404:
                    raise ApolloNotFoundError(f"Resource not found: {endpoint}")
                elif response.status_code == 422:
                    error_data = response.json()
                    raise ApolloValidationError(
                        f"Validation error: {error_data.get('error', 'Unknown')}"
                    )
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise ApolloError("Request timeout. Apollo API may be slow.")
            except requests.exceptions.RequestException as e:
                raise ApolloError(f"Request failed: {str(e)}")
        
        return {}
    
    def enrich_person(
        self,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        name: Optional[str] = None,
        organization_name: Optional[str] = None,
        domain: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        reveal_personal_emails: bool = False,
        reveal_phone_number: bool = False
    ) -> Dict:
        """
        Enrich a single person's data
        
        Args:
            email: Professional email address
            first_name: First name
            last_name: Last name
            name: Full name (alternative to first/last)
            organization_name: Company name
            domain: Company domain
            linkedin_url: LinkedIn profile URL
            reveal_personal_emails: Include personal emails (uses more credits)
            reveal_phone_number: Include phone numbers (uses more credits)
            
        Returns:
            Enriched person data with organization info
        """
        # Build request data with provided identifiers
        data = {}
        
        if email:
            data['email'] = email
        if first_name:
            data['first_name'] = first_name
        if last_name:
            data['last_name'] = last_name
        if name:
            # Parse full name into components
            name_parts = name.split(maxsplit=1)
            if len(name_parts) == 2 and not first_name:
                data['first_name'] = name_parts[0]
                data['last_name'] = name_parts[1]
        if organization_name:
            data['organization_name'] = organization_name
        if domain:
            data['domain'] = domain
        if linkedin_url:
            data['linkedin_url'] = linkedin_url
        
        # Add reveal flags
        if reveal_personal_emails:
            data['reveal_personal_emails'] = True
        if reveal_phone_number:
            data['reveal_phone_number'] = True
        
        if not data:
            return {'status': 'error', 'error': 'No identifiers provided'}
        
        try:
            result = self._make_request('POST', '/people/match', data=data)
            
            if result.get('person'):
                return {
                    'status': 'success',
                    'data': result.get('person', {}),
                    'credits_used': 1,
                    'match_confidence': result.get('confidence_score', 'unknown')
                }
            else:
                return {
                    'status': 'not_found',
                    'data': {},
                    'credits_used': 0,
                    'message': 'Person not found in Apollo database'
                }
                
        except ApolloNotFoundError:
            return {
                'status': 'not_found',
                'data': {},
                'credits_used': 0
            }
        except ApolloError as e:
            return {
                'status': 'error',
                'error': str(e),
                'data': {}
            }
    
    def search_people(
        self,
        titles: Optional[List[str]] = None,
        company_name: Optional[str] = None,
        company_domains: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        limit: int = 10,
        page: int = 1
    ) -> Dict:
        """
        Search for people in Apollo's database
        
        Args:
            titles: List of job titles (e.g., ["CEO", "CTO"])
            company_name: Company name to search
            company_domains: List of company domains
            locations: Geographic locations
            industries: Industry categories
            keywords: General search keywords
            limit: Results per page (max 100)
            page: Page number for pagination
            
        Returns:
            Search results with people and pagination info
        """
        data = {
            'per_page': min(limit, 100),
            'page': page
        }
        
        # Build person filters
        person_filters = {}
        if titles:
            person_filters['titles'] = titles
        if locations:
            person_filters['locations'] = locations
        
        if person_filters:
            data['person_filters'] = person_filters
        
        # Build organization filters
        org_filters = {}
        if company_name:
            org_filters['name'] = company_name
        if company_domains:
            org_filters['domain'] = company_domains
        if industries:
            org_filters['industry'] = industries
        
        if org_filters:
            data['organization_filters'] = org_filters
        
        if keywords:
            data['q_keywords'] = keywords
        
        try:
            result = self._make_request('POST', '/mixed_people/search', data=data)
            
            return {
                'status': 'success',
                'people': result.get('people', []),
                'total_entries': result.get('total_entries', 0),
                'total_pages': result.get('pagination', {}).get('total_pages', 0),
                'current_page': page,
                'credits_used': 1
            }
            
        except ApolloError as e:
            return {
                'status': 'error',
                'error': str(e),
                'people': []
            }
    
    def enrich_organization(
        self,
        domain: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict:
        """
        Enrich organization/company data
        
        Args:
            domain: Company website domain (e.g., "apollo.io")
            name: Company name
            
        Returns:
            Enriched organization data
        """
        if not domain and not name:
            return {'status': 'error', 'error': 'Domain or name required'}
        
        data = {}
        if domain:
            data['domain'] = domain
        if name:
            data['name'] = name
        
        try:
            result = self._make_request('POST', '/organizations/enrich', data=data)
            
            if result.get('organization'):
                return {
                    'status': 'success',
                    'data': result.get('organization', {}),
                    'credits_used': 1
                }
            else:
                return {
                    'status': 'not_found',
                    'data': {},
                    'credits_used': 0
                }
                
        except ApolloError as e:
            return {
                'status': 'error',
                'error': str(e),
                'data': {}
            }
    
    def bulk_enrich_people(
        self,
        people: List[Dict],
        chunk_size: int = 10
    ) -> List[Dict]:
        """
        Enrich multiple people in batches
        
        Args:
            people: List of person dicts with email, name, etc.
            chunk_size: Number of people per batch (max 10)
            
        Returns:
            List of enrichment results
        """
        results = []
        
        for i in range(0, len(people), chunk_size):
            chunk = people[i:i + chunk_size]
            
            for person_data in chunk:
                result = self.enrich_person(**person_data)
                results.append({
                    'input': person_data,
                    'result': result
                })
            
            # Rate limiting - be nice to the API
            if i + chunk_size < len(people):
                time.sleep(0.5)
        
        return results
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status"""
        return {
            'remaining': self.rate_limit_remaining,
            'reset_time': self.rate_limit_reset
        }


def main():
    """CLI interface for Apollo client"""
    parser = argparse.ArgumentParser(description='Apollo.io Lead Enrichment CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Enrich command
    enrich_parser = subparsers.add_parser('enrich', help='Enrich a person')
    enrich_parser.add_argument('--email', help='Email address')
    enrich_parser.add_argument('--first-name', help='First name')
    enrich_parser.add_argument('--last-name', help='Last name')
    enrich_parser.add_argument('--company', help='Company name')
    enrich_parser.add_argument('--domain', help='Company domain')
    enrich_parser.add_argument('--reveal-emails', action='store_true', help='Reveal personal emails')
    enrich_parser.add_argument('--reveal-phone', action='store_true', help='Reveal phone numbers')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for people')
    search_parser.add_argument('--titles', nargs='+', help='Job titles')
    search_parser.add_argument('--company', help='Company name')
    search_parser.add_argument('--domains', nargs='+', help='Company domains')
    search_parser.add_argument('--locations', nargs='+', help='Locations')
    search_parser.add_argument('--limit', type=int, default=10, help='Result limit')
    
    # Enrich org command
    org_parser = subparsers.add_parser('org', help='Enrich organization')
    org_parser.add_argument('--domain', help='Company domain')
    org_parser.add_argument('--name', help='Company name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        client = ApolloClient()
        
        if args.command == 'enrich':
            result = client.enrich_person(
                email=args.email,
                first_name=args.first_name,
                last_name=args.last_name,
                organization_name=args.company,
                domain=args.domain,
                reveal_personal_emails=args.reveal_emails,
                reveal_phone_number=args.reveal_phone
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == 'search':
            result = client.search_people(
                titles=args.titles,
                company_name=args.company,
                company_domains=args.domains,
                locations=args.locations,
                limit=args.limit
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == 'org':
            result = client.enrich_organization(
                domain=args.domain,
                name=args.name
            )
            print(json.dumps(result, indent=2))
            
    except ApolloAuthError as e:
        print(f"Authentication error: {e}", file=sys.stderr)
        sys.exit(1)
    except ApolloError as e:
        print(f"API error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
