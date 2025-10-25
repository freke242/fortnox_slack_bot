import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

#!/usr/bin/env python3
"""
Test script to discover and map Fortnox price lists.

This script lists all price lists from Fortnox and maps their names to IDs.
Expected price lists: A, B, C with names Systembolaget, HoReCa, Kranen
"""
import os
import logging
from dotenv import load_dotenv
from src.fortnox_client import FortnoxClient, FortnoxRateLimitError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to test price list discovery"""
    logger.info("=" * 70)
    logger.info("Fortnox Price Lists Discovery Test")
    logger.info("=" * 70)
    
    # Load environment variables
    load_dotenv()
    
    # Get initial access token (will be refreshed if needed)
    access_token = os.environ.get("FORTNOX_ACCESS_TOKEN")
    client_secret = os.environ.get("FORTNOX_CLIENT_SECRET")
    
    if not access_token or not client_secret:
        logger.error("Missing FORTNOX_ACCESS_TOKEN or FORTNOX_CLIENT_SECRET")
        logger.error("Please check your .env file")
        return
    
    # Initialize Fortnox client
    logger.info("Initializing Fortnox client...")
    client = FortnoxClient(
        access_token=access_token,
        client_secret=client_secret
    )
    
    try:
        # Get a sample beer keg article to test with
        logger.info("\n📦 Finding a sample beer keg article...")
        kegs = client.get_beer_kegs_in_stock()
        
        if not kegs:
            logger.error("No beer kegs found in stock. Cannot test price lists.")
            return
        
        # Test each expected price list code with multiple articles
        logger.info("\n🔍 Testing price list codes A, B, C with multiple articles...")
        
        price_list_codes = ["A", "B", "C"]
        expected_names = {
            "A": "Systembolaget",
            "B": "HoReCa",
            "C": "Kranen"
        }
        
        # First, show all kegs and their article numbers
        logger.info("\n📋 Available beer kegs:")
        print("\n" + "=" * 70)
        print(f"{'Article #':<15} {'Name':<30} {'SalesPrice':<10}")
        print("-" * 70)
        for keg in kegs[:15]:  # Show first 15
            print(f"{keg['article_number']:<15} {keg['name'][:29]:<30} {keg['price']:<10.2f}")
        print("=" * 70)
        
        # Find BFG 2026 specifically
        bfg_2026 = None
        for keg in kegs:
            if "BFG 2026" in keg['name'] or "bfg 2026" in keg['name'].lower():
                bfg_2026 = keg
                logger.info(f"\n🎯 Found BFG 2026: Article {keg['article_number']}")
                break
        
        if bfg_2026:
            logger.info(f"\n🔍 Testing price lists specifically for BFG 2026 (Article: {bfg_2026['article_number']})...")
            print("\n" + "=" * 70)
            print(f"Testing BFG 2026 (Article: {bfg_2026['article_number']})")
            print("-" * 70)
            
            for code in price_list_codes:
                try:
                    logger.info(f"Fetching prices/{code}/{bfg_2026['article_number']}")
                    response = client._make_request("GET", f"prices/{code}/{bfg_2026['article_number']}")
                    
                    print(f"\nPrice List {code} ({expected_names[code]}):")
                    
                    price_data = response.get("Price", {})
                    if price_data:
                        price_value = price_data.get('Price', 0)
                        from_qty = price_data.get('FromQuantity', 0)
                        print(f"  ✅ Price found: {price_value}")
                        print(f"  FromQuantity: {from_qty}")
                    else:
                        print(f"  ⚠️  No price data in response")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "404" in error_msg:
                        print(f"  404 - Price list entry not found")
                    else:
                        print(f"  Error: {error_msg}")
                    logger.error(f"Full error: {e}", exc_info=True)
            
            print("=" * 70)
        
        # Try to find articles with prices in each list
        price_list_results = {code: [] for code in price_list_codes}
        
        logger.info(f"\n🔍 Testing all kegs with price lists...")
        
        for keg in kegs[:5]:  # Test first 5 to avoid rate limit
            article_number = keg['article_number']
            article_name = keg['name']
            
            for code in price_list_codes:
                try:
                    response = client._make_request("GET", f"prices/{code}/{article_number}")
                    price_data = response.get("Price", {})
                    
                    if price_data:
                        price = float(price_data.get("Price", 0) or 0)
                        if price > 0:
                            price_list_results[code].append({
                                'article': article_number,
                                'name': article_name,
                                'price': price
                            })
                            logger.debug(f"  Found price for {article_name} in list {code}: {price}")
                except Exception as e:
                    # Silent fail - just looking for which articles have prices
                    pass
        
        # Display results
        print("\n" + "=" * 70)
        print("Price List Discovery Results")
        print("=" * 70)
        
        found_any = False
        for code in price_list_codes:
            articles_with_prices = price_list_results[code]
            print(f"\nPrice List {code} ({expected_names[code]}):")
            print("-" * 70)
            
            if articles_with_prices:
                found_any = True
                print(f"{'Article':<15} {'Name':<30} {'Price':<10}")
                print("-" * 70)
                for item in articles_with_prices[:5]:  # Show first 5
                    print(f"{item['article']:<15} {item['name'][:29]:<30} {item['price']:<10.2f}")
                if len(articles_with_prices) > 5:
                    print(f"... and {len(articles_with_prices) - 5} more")
            else:
                print("  ⚠️  No prices found for tested articles")
        
        print("=" * 70)
        
        # Summary
        if found_any:
            logger.info("\n✅ Price lists found and accessible!")
            logger.info("\n📊 Price List Mapping:")
            print("\n" + "=" * 70)
            print("Price List Configuration for Beer Kegs")
            print("-" * 70)
            for code in price_list_codes:
                count = len(price_list_results[code])
                status = f"{count} articles with prices" if count > 0 else "No prices set"
                print(f"{expected_names[code]:<20} -> Code: {code:<5} ({status})")
            print("=" * 70)
        else:
            logger.warning("\n⚠️  No prices found in any price lists for the tested kegs")
        
    except FortnoxRateLimitError as e:
        logger.warning(f"\n⚠️  Test stopped - Rate limit exceeded!")
        logger.warning(f"{str(e)}")
        logger.warning("\nThe Fortnox API has a limit of 300 requests per minute.")
        logger.warning("Please wait a few minutes before running tests again.")
    except Exception as e:
        logger.error(f"Error fetching price lists: {e}", exc_info=True)


if __name__ == "__main__":
    main()
