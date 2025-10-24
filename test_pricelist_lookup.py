#!/usr/bin/env python3
"""
Test if we can query pricelists endpoint to map name to code
"""
import os
from dotenv import load_dotenv
from fortnox_client import FortnoxClient, FortnoxRateLimitError

load_dotenv()

client = FortnoxClient(
    access_token=os.environ.get("FORTNOX_ACCESS_TOKEN"),
    client_secret=os.environ.get("FORTNOX_CLIENT_SECRET")
)

try:
    response = client._make_request("GET", "pricelists")
    price_lists = response.get("PriceLists", [])
    
    print(f"\nFound {len(price_lists)} price lists:\n")
    print(f"{'Code':<10} {'Description':<30}")
    print("-" * 40)
    
    for pl in price_lists:
        code = pl.get("Code", "N/A")
        description = pl.get("Description", "N/A")
        print(f"{code:<10} {description:<30}")
        
        # Check if we can find HoReCa
        if "horeca" in description.lower():
            print(f"\n✅ Found HoReCa with code: {code}")
            
except FortnoxRateLimitError as e:
    print(f"\n⚠️  Test stopped - Rate limit exceeded!")
    print(f"{str(e)}")
    print("\nThe Fortnox API has a limit of 300 requests per minute.")
    print("Please wait a few minutes before running tests again.")
except Exception as e:
    print(f"Error: {e}")
