"""
Fortnox API Client
Handles all communication with the Fortnox API
"""
import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FortnoxClient:
    """Client for interacting with the Fortnox API"""
    
    BASE_URL = "https://api.fortnox.se/3"
    
    def __init__(self, access_token: str, client_secret: str):
        """
        Initialize the Fortnox API client
        
        Works with Fortnox service accounts for secure server-to-server integration.
        Service accounts are tied to a dedicated system user rather than a person.
        
        Args:
            access_token: Fortnox API access token (obtained via OAuth with service account)
            client_secret: Fortnox API client secret (from Developer Portal)
        
        Note:
            For service accounts, obtain the access token by:
            1. Enable "Only administrator" in Developer Portal
            2. Add account_type=service parameter to OAuth authorization URL
            3. Have a system administrator authorize the integration
        """
        self.access_token = access_token
        self.client_secret = client_secret
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Client-Secret": self.client_secret,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict:
        """
        Make an HTTP request to the Fortnox API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Fortnox API request failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_articles(self, filter_params: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve a list of articles from Fortnox
        
        Args:
            filter_params: Optional filters like articlenumber, description, etc.
            
        Returns:
            List of article dictionaries
        """
        logger.info("Fetching articles from Fortnox")
        response = self._make_request("GET", "articles", params=filter_params)
        articles = response.get("Articles", [])
        logger.info(f"Retrieved {len(articles)} articles")
        return articles
    
    def get_article_by_number(self, article_number: str) -> Dict:
        """
        Retrieve a specific article by article number
        
        Args:
            article_number: The article number to retrieve
            
        Returns:
            Article data dictionary
        """
        logger.info(f"Fetching article {article_number} from Fortnox")
        response = self._make_request("GET", f"articles/{article_number}")
        return response.get("Article", {})
    
    def get_articles_in_stock(self, minimum_stock: int = 0) -> List[Dict]:
        """
        Retrieve articles that are in stock
        
        Args:
            minimum_stock: Minimum stock quantity to filter by (default: 0, meaning any stock > 0)
            
        Returns:
            List of articles with stock information
        """
        logger.info(f"Fetching articles in stock (minimum: {minimum_stock})")
        articles = self.get_articles()
        
        # Filter articles that have stock
        articles_in_stock = []
        for article in articles:
            stock_quantity = article.get("QuantityInStock", 0)
            if stock_quantity > minimum_stock:
                articles_in_stock.append({
                    "ArticleNumber": article.get("ArticleNumber", "N/A"),
                    "Description": article.get("Description", "No description"),
                    "QuantityInStock": stock_quantity,
                    "Unit": article.get("Unit", "pcs"),
                    "StockPlace": article.get("StockPlace", "N/A"),
                    "SalesPrice": article.get("SalesPrice", 0),
                })
        
        logger.info(f"Found {len(articles_in_stock)} articles in stock")
        return articles_in_stock
