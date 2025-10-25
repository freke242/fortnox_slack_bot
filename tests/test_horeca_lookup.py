import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

#!/usr/bin/env python3
"""
Test HoReCa price list dynamic lookup
"""
import os
from dotenv import load_dotenv
from src.fortnox_client import FortnoxClient, FortnoxRateLimitError

load_dotenv()

print("Testing HoReCa price list lookup...")

# Create client
client = FortnoxClient(
    access_token=os.environ.get("FORTNOX_ACCESS_TOKEN"),
    client_secret=os.environ.get("FORTNOX_CLIENT_SECRET")
)

print(f"Before initialization: horeca_pricelist_code = {client.horeca_pricelist_code}")

# Initialize price lists
try:
    client.initialize_price_lists()
    print(f"After initialization: horeca_pricelist_code = {client.horeca_pricelist_code}")
    print(f"\n✅ Successfully found HoReCa price list with code: {client.horeca_pricelist_code}")
    
    # Test getting a keg price
    print("\nTesting keg retrieval with HoReCa prices...")
    kegs = client.get_beer_kegs_in_stock()
    
    if kegs:
        print(f"\nFound {len(kegs)} kegs:")
        for keg in kegs[:3]:
            print(f"  {keg['name']} - Price: {keg['price']}")
    
except FortnoxRateLimitError as e:
    print(f"\n⚠️  Test stopped - Rate limit exceeded!")
    print(f"{str(e)}")
    print("\nThe Fortnox API has a limit of 300 requests per minute.")
    print("Please wait a few minutes before running tests again.")
except ValueError as e:
    print(f"\n❌ Error: {e}")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
