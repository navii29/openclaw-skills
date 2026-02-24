#!/usr/bin/env python3
"""
A2A Market Client - Handles skill marketplace operations with x402 payments.

Improvements:
- Structured logging
- Retry logic with exponential backoff
- Circuit breaker pattern
- Proper type hints (Callable instead of callable)
- Connection pooling
- Request timeout handling

Usage:
    from a2a_client import A2AClient
    
    client = A2AClient(
        wallet_address="0x...",
        private_key=os.getenv("A2A_MARKET_PRIVATE_KEY"),
        api_url="https://api.a2amarket.live"
    )
    
    # Search skills
    results = client.search("pdf parser", max_price=10)
    
    # Purchase skill
    skill = client.purchase("skill_042")
"""

import os
import sys
import json
import time
import logging
import hashlib
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from eth_account import Account
from eth_account.messages import encode_defunct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('a2a_market')

API_URL = os.getenv("A2A_MARKET_API_URL", "https://api.a2amarket.live")

AGENT_ID_FILE = os.path.expanduser("~/.a2a_agent_id")
REFERRAL_CODE_FILE = os.path.expanduser("~/.a2a_referral_code")


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for API resilience"""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    
    def __post_init__(self):
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time: Optional[float] = None
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - (self.last_failure_time or 0) > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
                return True
            return False
        return True
    
    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker CLOSED - service recovered")
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(f"Circuit breaker OPEN after {self.failures} failures")
            self.state = CircuitState.OPEN


@dataclass
class SpendingRules:
    max_per_transaction: float = 10.0
    daily_budget: float = 100.0
    min_seller_reputation: int = 60
    auto_approve_below: float = 5.0
    require_confirmation_above: float = 50.0


@dataclass
class Skill:
    id: str
    name: str
    description: str
    price: float
    seller: str
    reputation: int
    rating: float
    sales: int


def retry_on_error(max_retries: int = 3, delay: float = 1.0, 
                   exceptions: tuple = (requests.RequestException,),
                   backoff_factor: float = 2.0):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator


class A2AClient:
    """Enhanced A2A Market client with resilience patterns"""
    
    def __init__(
        self,
        wallet_address: str,
        private_key: str,
        api_url: str = API_URL,
        spending_rules: Optional[SpendingRules] = None,
        agent_id: Optional[str] = None
    ):
        if not wallet_address or not private_key:
            raise ValueError("wallet_address and private_key are required")
        
        self.wallet_address = wallet_address
        self.api_url = api_url.rstrip('/')
        self.rules = spending_rules or SpendingRules()
        self.daily_spent = 0.0
        self.agent_id = agent_id or self._load_agent_id()
        self.circuit_breaker = CircuitBreaker()
        
        # Initialize Ethereum account
        try:
            self.account = Account.from_key(private_key)
        except Exception as e:
            raise ValueError(f"Invalid private key: {e}")
        
        # Setup session with connection pooling and retries
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        
        logger.info(f"A2AClient initialized for wallet {wallet_address[:10]}...")
    
    def _load_agent_id(self) -> Optional[str]:
        """Load agent_id from environment or file"""
        agent_id = os.getenv("A2A_AGENT_ID")
        if agent_id:
            return agent_id
        if os.path.exists(AGENT_ID_FILE):
            try:
                with open(AGENT_ID_FILE) as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Failed to load agent_id from file: {e}")
        return None
    
    def _agent_headers(self) -> Dict[str, str]:
        """Get headers with agent ID for Credits API calls"""
        if not self.agent_id:
            raise ValueError("Agent ID required. Call register() first.")
        return {"x-agent-id": self.agent_id}
    
    def _sign_request(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Sign API request for authentication"""
        timestamp = str(int(time.time() * 1000))
        body_hash = hashlib.sha256(body.encode()).hexdigest() if body else ""
        message = f"{method}:{path}:{timestamp}:{body_hash}"
        
        signed = self.account.sign_message(encode_defunct(text=message))
        
        return {
            "X-Wallet-Address": self.wallet_address,
            "X-Timestamp": timestamp,
            "X-Signature": signed.signature.hex()
        }
    
    def _check_budget(self, price: float) -> tuple[bool, str]:
        """Check if purchase is within budget rules"""
        if price > self.rules.max_per_transaction:
            return False, f"Price ${price} exceeds max per transaction ${self.rules.max_per_transaction}"
        
        if self.daily_spent + price > self.rules.daily_budget:
            return False, f"Would exceed daily budget (spent: ${self.daily_spent}, limit: ${self.rules.daily_budget})"
        
        return True, "OK"
    
    def _needs_confirmation(self, price: float) -> bool:
        """Check if purchase needs human confirmation"""
        return price > self.rules.auto_approve_below
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with circuit breaker"""
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN - API temporarily unavailable")
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=30,
                **kwargs
            )
            self.circuit_breaker.record_success()
            return response
            
        except requests.RequestException as e:
            self.circuit_breaker.record_failure()
            raise
    
    @retry_on_error(max_retries=3, delay=1.0)
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        min_rep: Optional[int] = None,
        max_price: Optional[float] = None,
        sort: str = "rating",
        limit: int = 20
    ) -> List[Skill]:
        """Search for skills on the marketplace with retry logic"""
        params = {"q": query, "sort": sort, "limit": limit}
        
        if category:
            params["category"] = category
        if min_rep is not None:
            params["min_rep"] = min_rep
        else:
            params["min_rep"] = self.rules.min_seller_reputation
        if max_price is not None:
            params["max_price"] = max_price
        
        response = self._make_request("GET", "/v1/listings/search", params=params)
        response.raise_for_status()
        
        data = response.json()
        return [
            Skill(
                id=r["id"],
                name=r["name"],
                description=r.get("description", ""),
                price=r["price"],
                seller=r["seller"],
                reputation=r.get("reputation", 0),
                rating=r.get("rating", 0),
                sales=r.get("sales", 0)
            )
            for r in data.get("results", [])
        ]
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_skill(self, skill_id: str) -> Dict[str, Any]:
        """Get detailed information about a skill"""
        if not skill_id:
            raise ValueError("skill_id is required")
        
        response = self._make_request("GET", f"/v1/listings/{skill_id}")
        response.raise_for_status()
        return response.json()
    
    def purchase(
        self,
        skill_id: str,
        confirm_callback: Optional[Callable[[Skill], bool]] = None,
        payment_method: str = "x402"
    ) -> Dict[str, Any]:
        """
        Purchase a skill using x402 payment or credits
        
        Args:
            skill_id: ID of the skill to purchase
            confirm_callback: Optional callback for confirmation (returns True to proceed)
            payment_method: "x402" for USDC payment, "credits" for credits payment
        
        Returns:
            Skill content if successful
        """
        if payment_method == "credits":
            return self.purchase_with_credits(skill_id)
        
        # Get skill details first
        skill_data = self.get_skill(skill_id)
        price = skill_data["price"]
        skill = Skill(
            id=skill_data["id"],
            name=skill_data["name"],
            description=skill_data.get("description", ""),
            price=price,
            seller=skill_data.get("seller", ""),
            reputation=skill_data.get("reputation", 0),
            rating=skill_data.get("rating", 0),
            sales=skill_data.get("sales", 0)
        )
        
        # Check seller reputation
        seller_rep = skill_data.get("seller", {}).get("reputation", 0)
        if seller_rep < self.rules.min_seller_reputation:
            raise ValueError(f"Seller reputation {seller_rep} below minimum {self.rules.min_seller_reputation}")
        
        # Check budget
        ok, msg = self._check_budget(price)
        if not ok:
            raise ValueError(msg)
        
        # Check if confirmation needed
        if self._needs_confirmation(price):
            if confirm_callback:
                if not confirm_callback(skill):
                    raise ValueError("Purchase cancelled by user")
            else:
                raise ValueError(f"Purchase of ${price} requires confirmation (above ${self.rules.auto_approve_below})")
        
        # Step 1: Request content, expect 402
        response = self._make_request("GET", f"/v1/listings/{skill_id}/content")
        
        if response.status_code != 402:
            if response.status_code == 200:
                # Already purchased or free
                return response.json()
            response.raise_for_status()
        
        # Step 2: Parse payment requirements
        payment_info = json.loads(response.headers.get("X-Payment-Required", "{}"))
        
        # Step 3: Sign payment
        payment_proof = self._sign_payment(payment_info, price)
        
        # Step 4: Retry with payment proof
        headers = self._sign_request("POST", f"/v1/listings/{skill_id}/content")
        headers["X-Payment"] = payment_proof
        headers["Content-Type"] = "application/json"
        
        response = self._make_request(
            "POST",
            f"/v1/listings/{skill_id}/content",
            headers=headers
        )
        response.raise_for_status()
        
        # Update daily spent
        self.daily_spent += price
        logger.info(f"Purchase successful: {skill.name} for ${price}")
        
        return response.json()
    
    def _sign_payment(self, payment_info: Dict, price: float) -> str:
        """
        Sign x402 payment
        Note: Simplified implementation. Real x402 uses ERC-3009 TransferWithAuthorization
        """
        payment_data = {
            "from": self.wallet_address,
            "to": payment_info.get("accepts", [{}])[0].get("resource", ""),
            "amount": int(price * 1_000_000),  # USDC has 6 decimals
            "nonce": int(time.time() * 1000),
            "deadline": int(time.time()) + 3600  # 1 hour validity
        }
        
        message = json.dumps(payment_data, sort_keys=True)
        signed = self.account.sign_message(encode_defunct(text=message))
        
        return json.dumps({
            "payment": payment_data,
            "signature": signed.signature.hex()
        })
    
    @retry_on_error(max_retries=3, delay=1.0)
    def list_skill(
        self,
        name: str,
        description: str,
        price: float,
        category: str,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """List a new skill for sale with validation"""
        if not name or len(name) < 3:
            raise ValueError("Name must be at least 3 characters")
        if price <= 0:
            raise ValueError("Price must be positive")
        if not category:
            raise ValueError("Category is required")
        
        body = json.dumps({
            "name": name,
            "description": description,
            "price": price,
            "category": category,
            "content": content,
            "tags": tags or []
        })
        
        headers = self._sign_request("POST", "/v1/listings", body)
        headers["Content-Type"] = "application/json"
        
        response = self._make_request(
            "/v1/listings",
            method="POST",
            headers=headers,
            data=body
        )
        response.raise_for_status()
        
        return response.json()
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_earnings(self) -> Dict[str, Any]:
        """Get account earnings summary"""
        response = self._make_request("GET", f"/v1/account/{self.wallet_address}/earnings")
        response.raise_for_status()
        return response.json()
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_purchases(self) -> List[Dict[str, Any]]:
        """Get list of purchased skills"""
        response = self._make_request("GET", f"/v1/account/{self.wallet_address}/purchases")
        response.raise_for_status()
        return response.json().get("purchases", [])
    
    @retry_on_error(max_retries=3, delay=1.0)
    def register(self, name: str) -> Dict[str, Any]:
        """
        Register as an agent and receive initial credits
        
        Args:
            name: Display name for the agent
        
        Returns:
            {"agent_id": "...", "referral_code": "...", "credits": {"balance": 100}}
        """
        if not name or len(name) < 2:
            raise ValueError("Name must be at least 2 characters")
        
        body = json.dumps({
            "wallet_address": self.wallet_address,
            "name": name
        })
        
        response = self._make_request(
            "POST",
            "/v1/agents/register",
            headers={"Content-Type": "application/json"},
            data=body
        )
        response.raise_for_status()
        data = response.json()
        
        # Save agent_id and referral_code locally
        self.agent_id = data["agent_id"]
        try:
            os.makedirs(os.path.dirname(AGENT_ID_FILE), exist_ok=True)
            with open(AGENT_ID_FILE, "w") as f:
                f.write(self.agent_id)
            with open(REFERRAL_CODE_FILE, "w") as f:
                f.write(data.get("referral_code", ""))
        except Exception as e:
            logger.warning(f"Failed to save credentials: {e}")
        
        logger.info(f"Agent registered: {self.agent_id}")
        return data
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_credits_balance(self) -> Dict[str, Any]:
        """Get credits balance"""
        response = self._make_request(
            "GET",
            "/v1/credits/balance",
            headers=self._agent_headers()
        )
        response.raise_for_status()
        return response.json()
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_daily_reward_status(self) -> Dict[str, Any]:
        """Check daily reward status"""
        response = self._make_request(
            "GET",
            "/v1/rewards/daily/status",
            headers=self._agent_headers()
        )
        response.raise_for_status()
        return response.json()
    
    @retry_on_error(max_retries=3, delay=1.0)
    def claim_daily_reward(self) -> Dict[str, Any]:
        """Claim the daily reward credits"""
        response = self._make_request(
            "POST",
            "/v1/rewards/daily/claim",
            headers=self._agent_headers()
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"Daily reward claimed: {data.get('claimed')} credits")
        return data
    
    @retry_on_error(max_retries=3, delay=1.0)
    def purchase_with_credits(self, skill_id: str) -> Dict[str, Any]:
        """Purchase a skill using credits instead of USDC"""
        if not skill_id:
            raise ValueError("skill_id is required")
        
        headers = self._agent_headers()
        headers["Content-Type"] = "application/json"
        
        response = self._make_request(
            "POST",
            f"/v1/listings/{skill_id}/pay",
            headers=headers,
            data=json.dumps({"payment_method": "credits"})
        )
        response.raise_for_status()
        return response.json()
    
    @retry_on_error(max_retries=3, delay=1.0)
    def get_price_suggestion(
        self,
        skill_name: str,
        category: str,
        description: str = "",
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get price suggestion for a new skill listing"""
        body = json.dumps({
            "skill_name": skill_name,
            "category": category,
            "description": description,
            "keywords": keywords or [],
            "seller_reputation": 50  # Default for new sellers
        })
        
        response = self._make_request(
            "POST",
            "/v1/pricing/suggest",
            headers={"Content-Type": "application/json"},
            data=body
        )
        response.raise_for_status()
        return response.json()
    
    def list_skill_with_suggestion(
        self,
        name: str,
        description: str,
        category: str,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None,
        price: Optional[float] = None,
        confirm_callback: Optional[Callable[[str, Dict], bool]] = None
    ) -> Dict[str, Any]:
        """
        List a skill with automatic price suggestion if no price provided
        """
        if price is None:
            suggestion = self.get_price_suggestion(
                skill_name=name,
                category=category,
                description=description,
                keywords=tags
            )
            
            recommended = suggestion["suggested_range"]["recommended"]
            confidence = suggestion["confidence"]
            
            if confidence == "low" and confirm_callback:
                msg = (f"No market data for '{name}'. "
                       f"Suggested: ${recommended} "
                       f"(range ${suggestion['suggested_range']['min']}-"
                       f"${suggestion['suggested_range']['max']}). Proceed?")
                if not confirm_callback(msg, suggestion):
                    raise ValueError("Listing cancelled by user")
            
            price = recommended
            logger.info(f"Using suggested price: ${price} (confidence: {confidence})")
        
        return self.list_skill(name, description, price, category, content, tags)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "daily_spent": self.daily_spent,
            "daily_budget": self.rules.daily_budget,
            "agent_id": self.agent_id,
            "circuit_state": self.circuit_breaker.state.value,
            "circuit_failures": self.circuit_breaker.failures
        }


# Example usage
if __name__ == "__main__":
    import sys

    wallet = os.getenv("WALLET_ADDRESS")
    key = os.getenv("A2A_MARKET_PRIVATE_KEY")

    if not wallet or not key:
        print("Set WALLET_ADDRESS and A2A_MARKET_PRIVATE_KEY environment variables")
        sys.exit(1)

    try:
        client = A2AClient(wallet, key)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # Register (first time only)
    if not client.agent_id:
        print("Registering agent...")
        reg = client.register("My Agent")
        print(f"  Agent ID: {reg['agent_id']}")
        print(f"  Referral Code: {reg['referral_code']}")
        print(f"  Initial Credits: {reg['credits']['balance']}")

    # Check credits balance
    print("\nCredits balance...")
    balance = client.get_credits_balance()
    print(f"  Balance: {balance['balance']} credits")

    # Claim daily reward
    print("\nDaily reward...")
    status = client.get_daily_reward_status()
    if status["available"]:
        reward = client.claim_daily_reward()
        print(f"  Claimed {reward['claimed']} credits! Balance: {reward['new_balance']}")
    else:
        print(f"  Already claimed. Next: {status['next_available_at']}")

    # Search example
    print("\nSearching for 'code review' skills...")
    try:
        skills = client.search("code review", max_price=15)
        for s in skills[:5]:
            print(f"  [{s.id}] {s.name} - ${s.price} (rating:{s.rating}, rep:{s.reputation})")
    except Exception as e:
        print(f"  Error: {e}")

    # Check earnings
    print("\nChecking earnings...")
    try:
        earnings = client.get_earnings()
        print(f"  Total: ${earnings.get('total_earnings', 0)}")
        print(f"  Available: ${earnings.get('available', 0)}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Stats
    print("\nClient stats...")
    stats = client.get_stats()
    print(f"  Daily spent: ${stats['daily_spent']:.2f} / ${stats['daily_budget']:.2f}")
    print(f"  Circuit state: {stats['circuit_state']}")
