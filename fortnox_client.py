"""
Fortnox API Client
Handles all communication with the Fortnox API
"""
import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FortnoxRateLimitError(Exception):
    """Raised when Fortnox API rate limit is exceeded"""
    pass


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
        self.horeca_pricelist_code = None  # Will be set by initialize_price_lists()
        self.horeca_prices_cache = {}  # In-memory cache: {article_number: price}
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Client-Secret": self.client_secret,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def initialize_price_lists(self):
        """
        Initialize price lists by finding the HoReCa price list code and loading all prices into memory.
        If HoReCa price list is not found or cannot be loaded, falls back to using SalesPrice.
        Must be called after instantiation before using beer keg methods.
        
        Raises:
            FortnoxRateLimitError: If API rate limit is exceeded
        """
        logger.info("Initializing price lists...")
        try:
            response = self._make_request("GET", "pricelists")
            price_lists = response.get("PriceLists", [])
            
            # Find HoReCa price list
            for price_list in price_lists:
                description = price_list.get("Description", "")
                if "horeca" in description.lower():
                    self.horeca_pricelist_code = price_list.get("Code")
                    logger.info(f"✅ Found HoReCa price list with code: {self.horeca_pricelist_code}")
                    
                    # Load all prices from HoReCa price list into cache
                    self._load_pricelist_cache(self.horeca_pricelist_code)
                    return
            
            # If we get here, HoReCa was not found
            logger.warning("HoReCa price list not found in Fortnox")
            logger.warning("Bot will use SalesPrice for all kegs")
            # Don't raise - allow bot to function with fallback pricing
            
        except FortnoxRateLimitError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            logger.error(f"Failed to initialize price lists: {e}")
            raise
    
    def _load_pricelist_cache(self, price_list_code: str):
        """
        Load all prices from a price list into memory cache.
        This is called at startup and every 50 minutes when the token refreshes.
        
        Args:
            price_list_code: Price list code to load (e.g., "B")
        """
        logger.info(f"🔄 Refreshing price cache from price list {price_list_code}...")
        try:
            response = self._make_request("GET", f"prices/sublist/{price_list_code}")
            prices = response.get("Prices", [])
            
            # Build cache: article_number -> price
            for price_entry in prices:
                article_number = price_entry.get("ArticleNumber")
                price_value = price_entry.get("Price", 0)
                
                if article_number and price_value:
                    # Only cache the base price (FromQuantity = 0)
                    from_quantity = float(price_entry.get("FromQuantity", 0))
                    if from_quantity == 0:
                        self.horeca_prices_cache[article_number] = float(price_value)
            
            logger.info(f"✅ Cached {len(self.horeca_prices_cache)} prices from HoReCa price list")
            
        except FortnoxRateLimitError:
            # Re-raise rate limit errors - critical
            logger.error("Rate limit hit while loading price cache")
            raise
        except Exception as e:
            logger.warning(f"Could not load price list cache: {e}")
            logger.warning("Will fall back to SalesPrice for pricing")
            # Don't fail - we can fall back to SalesPrice
            self.horeca_prices_cache = {}
    
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
            
            # Check for rate limiting before raising for status
            if response.status_code == 429:
                logger.warning("⚠️  Fortnox API rate limit exceeded (429 Too Many Requests)")
                raise FortnoxRateLimitError("Fortnox API rate limit exceeded. Please wait a few minutes and try again.")
            
            response.raise_for_status()
            return response.json()
        except FortnoxRateLimitError:
            # Re-raise rate limit errors without wrapping
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Fortnox API request failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_articles(self, filter_params: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve a list of articles from Fortnox with pagination support
        
        Args:
            filter_params: Optional filters like articlenumber, description, etc.
            
        Returns:
            List of article dictionaries (all pages combined)
        """
        logger.info("Fetching articles from Fortnox with pagination")
        
        # Initialize pagination parameters
        limit = 500  # Maximum allowed by Fortnox API
        offset = 0
        all_articles = []
        
        # Merge filter params with pagination params
        if filter_params is None:
            filter_params = {}
        
        while True:
            # Set pagination parameters
            params = filter_params.copy()
            params['limit'] = limit
            params['offset'] = offset
            
            logger.info(f"Fetching page: offset={offset}, limit={limit}")
            response = self._make_request("GET", "articles", params=params)
            articles = response.get("Articles", [])
            
            if not articles:
                # No more articles to fetch
                logger.info("No more articles to fetch")
                break
            
            all_articles.extend(articles)
            logger.info(f"Retrieved {len(articles)} articles (total so far: {len(all_articles)})")
            
            # If we got fewer articles than the limit, we've reached the end
            if len(articles) < limit:
                logger.info("Reached last page of results")
                break
            
            # Move to next page
            offset += limit
        
        logger.info(f"Retrieved {len(all_articles)} total articles")
        return all_articles
    
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
    
    def get_price_from_pricelist(self, price_list: str, article_number: str) -> float:
        """
        Retrieve price for an article from a specific price list
        
        Args:
            price_list: Price list code (e.g., "A", "B", "C")
            article_number: The article number to get price for
            
        Returns:
            Price as float, or 0 if not found
            
        Raises:
            FortnoxRateLimitError: If API rate limit is exceeded
        """
        try:
            logger.debug(f"Fetching price for article {article_number} from price list {price_list}")
            response = self._make_request("GET", f"prices/{price_list}/{article_number}")
            
            # The response contains a single Price object (not an array)
            # Structure: {"Price": {"ArticleNumber": "...", "Price": 1700, "FromQuantity": 0, ...}}
            price_data = response.get("Price", {})
            if price_data:
                price_value = price_data.get("Price", 0)
                return float(price_value or 0)
            return 0.0
        except FortnoxRateLimitError:
            # Re-raise rate limit errors to stop processing immediately
            raise
        except Exception as e:
            logger.debug(f"Could not fetch price for {article_number} from {price_list}: {e}")
            return 0.0
    
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
            # Convert stock_quantity to float (API may return string or number)
            try:
                stock_quantity = float(article.get("QuantityInStock", 0) or 0)
            except (ValueError, TypeError):
                stock_quantity = 0
            
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
    
    def get_beer_kegs_in_stock(self) -> List[Dict]:
        """
        Retrieve beer kegs that are in stock
        
        Filters articles by Swedish naming format: öl/fat/[volume]/[name]/[ABV]
        where 'öl' = beer, 'fat' = keg
        
        Returns:
            List of keg dictionaries with name, abv, volume, and quantity
        """
        logger.info("Fetching beer kegs in stock")
        articles = self.get_articles()
        
        kegs_in_stock = []
        for article in articles:
            description = article.get("Description", "")
            
            # Skip if no description
            if not description:
                continue
            
            # Split description by slash
            parts = description.split('/')
            
            # Check if format matches: öl/fat/volume/name/abv
            if len(parts) >= 5 and parts[0].lower() == 'öl' and parts[1].lower() == 'fat':
                try:
                    # Extract volume (convert to int)
                    volume = int(parts[2])
                    
                    # Extract name (may contain slashes, so join remaining parts except last)
                    name = '/'.join(parts[3:-1])
                    
                    # Extract ABV (last part)
                    abv = parts[-1]
                    
                    # Get quantity in stock (total)
                    stock_quantity = float(article.get("QuantityInStock", 0) or 0)
                    
                    # Get reserved quantity
                    try:
                        reserved_quantity = float(article.get("ReservedQuantity", 0) or 0)
                    except (ValueError, TypeError):
                        reserved_quantity = 0
                    
                    # Calculate available quantity (stock - reserved)
                    available_quantity = stock_quantity - reserved_quantity
                    
                    # Get price from HoReCa price list cache (loaded at startup)
                    article_number = article.get("ArticleNumber", "")
                    price = self.horeca_prices_cache.get(article_number, 0.0)
                    
                    # Fallback to SalesPrice if no price in HoReCa cache
                    if price == 0:
                        try:
                            price = float(article.get("SalesPrice", 0) or 0)
                        except (ValueError, TypeError):
                            price = 0.0
                    
                    # Only include if in stock
                    if stock_quantity > 0:
                        kegs_in_stock.append({
                            "name": name,
                            "abv": abv,
                            "volume": volume,
                            "quantity": int(stock_quantity),
                            "reserved": int(reserved_quantity),
                            "available": int(available_quantity),
                            "price": price,
                            "article_number": article_number
                        })
                except (ValueError, TypeError) as e:
                    logger.debug(f"Skipping malformed keg description: {description} - {e}")
                    continue
        
        logger.info(f"Found {len(kegs_in_stock)} beer kegs in stock")
        return kegs_in_stock
