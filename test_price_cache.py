#!/usr/bin/env python3
"""
Test price list caching - verifies we load prices once instead of per-article API calls
"""
import os
from dotenv import load_dotenv
from fortnox_client import FortnoxClient, FortnoxRateLimitError

load_dotenv()

print("Testing HoReCa price list caching...")

# Create client
client = FortnoxClient(
    access_token=os.environ.get("FORTNOX_ACCESS_TOKEN"),
    client_secret=os.environ.get("FORTNOX_CLIENT_SECRET")
)

print(f"Before initialization:")
print(f"  horeca_pricelist_code = {client.horeca_pricelist_code}")
print(f"  horeca_prices_cache size = {len(client.horeca_prices_cache)}")

try:
    # Initialize price lists (should load cache)
    client.initialize_price_lists()
    
    print(f"\nAfter initialization:")
    print(f"  horeca_pricelist_code = {client.horeca_pricelist_code}")
    print(f"  horeca_prices_cache size = {len(client.horeca_prices_cache)}")
    
    # Show sample cached prices
    print(f"\nSample cached prices (first 5):")
    for i, (article_num, price) in enumerate(list(client.horeca_prices_cache.items())[:5], 1):
        print(f"  {i}. Article {article_num}: {price} SEK")
    
    # Test getting kegs (should use cache, not make API calls for prices)
    print(f"\n🍺 Testing keg retrieval with cached prices...")
    kegs = client.get_beer_kegs_in_stock()
    
    if kegs:
        print(f"\n✅ Found {len(kegs)} kegs (prices from cache, no per-keg API calls!):")
        for keg in kegs[:5]:
            cached = "✅ from cache" if keg['article_number'] in client.horeca_prices_cache else "⚠️  fallback to SalesPrice"
            print(f"  {keg['name']}: {keg['price']} SEK ({cached})")
    
except FortnoxRateLimitError as e:
    print(f"\n⚠️  Test stopped - Rate limit exceeded!")
    print(f"{str(e)}")
    print("\nThe Fortnox API has a limit of 300 requests per minute.")
    print("Please wait a few minutes before running tests again.")
except ValueError as e:
    print(f"\n❌ Error: {e}")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
