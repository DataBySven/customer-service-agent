import httpx
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

class GorgiasClient:
    """
    HTTP client for Gorgias API with rate limiting.
    
    Gorgias Rate Limits (API key): 40 requests per 20 seconds.
    """
    
    def __init__(
        self,
        domain: str,
        username: str,
        api_key: str,
        request_delay: float = 0.6
    ):
        """
        Initialize Gorgias client.
        
        Args:
            domain: Gorgias domain (e.g., 'mycompany.gorgias.com')
            username: API username (email)
            api_key: API key
            request_delay: Delay between requests in seconds (default 0.6s = ~33 req/20s)
        """
        self.base_url = f"https://{domain}/api"
        self.auth = httpx.BasicAuth(username, api_key)
        self._request_count = 0
        self._last_request_time = None
        self._request_delay = request_delay
        self._client = None
    
    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                base_url=self.base_url,
                auth=self.auth,
                timeout=60.0
            )
        return self._client
    
    def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()
    
    def _throttle(self):
        """Apply rate limiting delay."""
        if self._last_request_time:
            elapsed = (datetime.now(timezone.utc) - self._last_request_time).total_seconds()
            if elapsed < self._request_delay:
                time.sleep(self._request_delay - elapsed)
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        max_retries: int = 5
    ) -> Any:
        """
        Make HTTP request with rate limit handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., 'tickets', 'tickets/123')
            params: Query parameters
            max_retries: Maximum retry attempts
            
        Returns:
            Response JSON data
        """
        client = self._get_client()
        
        for attempt in range(max_retries + 1):
            self._throttle()
            self._last_request_time = datetime.now(timezone.utc)
            
            try:
                response = client.request(
                    method, f"/{endpoint.lstrip('/')}", params=params
                )
                self._request_count += 1
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = min(int(response.headers.get("Retry-After", 2 ** attempt)), 60)
                    print(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json() if response.status_code != 204 else None
                
            except Exception as e:
                if attempt == max_retries:
                    raise Exception(f"Gorgias API request failed: {e}")
                wait_time = 2 ** attempt
                print(f"Request failed, retrying in {wait_time}s... ({e})")
                time.sleep(wait_time)
        
        raise Exception(f"Gorgias API failed after {max_retries} retries")
    
    def paginate(
        self,
        endpoint: str,
        params: dict = None,
        limit: int = 100,
        max_pages: int = None
    ) -> List[Dict]:
        """
        Fetch all pages from a paginated endpoint.
        
        Args:
            endpoint: API endpoint
            params: Additional query parameters
            limit: Page size (max 100)
            max_pages: Optional limit on number of pages to fetch
            
        Returns:
            List of all items from all pages
        """
        all_items = []
        cursor = None
        params = {**(params or {}), "limit": limit}
        page_count = 0
        
        while True:
            if cursor:
                params["cursor"] = cursor
            
            data = self.request("GET", endpoint, params=params)
            items = data.get("data", [])
            all_items.extend(items)
            page_count += 1
            
            print(f"  Fetched page {page_count}: {len(items)} items (total: {len(all_items)})")
            
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break
            
            if max_pages and page_count >= max_pages:
                print(f"  Stopped at max_pages={max_pages}")
                break
        
        return all_items
    
    @property
    def request_count(self) -> int:
        """Get total request count."""
        return self._request_count
