import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

"""
Test script for Fortnox API connection
Run this to verify your Fortnox credentials are working
"""
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.fortnox_client import FortnoxClient, FortnoxRateLimitError

def test_fortnox_connection():
    """Test the Fortnox API connection and credentials"""
    
    print("🧪 Testing Fortnox API Connection")
    print("=" * 50)
    print()
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    access_token = os.getenv("FORTNOX_ACCESS_TOKEN")
    client_secret = os.getenv("FORTNOX_CLIENT_SECRET")
    
    if not access_token or not client_secret:
        print("❌ Error: Missing Fortnox credentials in .env file")
        print("   Please set FORTNOX_ACCESS_TOKEN and FORTNOX_CLIENT_SECRET")
        return False
    
    print("✅ Environment variables loaded")
    print(f"   Access Token: {access_token[:10]}..." if len(access_token) > 10 else "   Access Token: ***")
    print(f"   Client Secret: {client_secret[:10]}..." if len(client_secret) > 10 else "   Client Secret: ***")
    print()
    
    try:
        # Initialize client
        print("🔌 Connecting to Fortnox API...")
        client = FortnoxClient(access_token, client_secret)
        print("✅ Client initialized")
        print()
        
        # Test fetching articles
        print("📦 Fetching articles...")
        articles = client.get_articles()
        print(f"✅ Successfully retrieved {len(articles)} articles")
        print()
        
        # Test filtering articles in stock
        print("🔍 Filtering articles in stock...")
        articles_in_stock = client.get_articles_in_stock()
        print(f"✅ Found {len(articles_in_stock)} articles in stock")
        print()
        
        # Display sample articles
        if articles_in_stock:
            print("📋 Sample articles (first 5):")
            print("-" * 50)
            for i, article in enumerate(articles_in_stock[:5], 1):
                print(f"{i}. {article['ArticleNumber']}: {article['Description']}")
                print(f"   Stock: {article['QuantityInStock']} {article['Unit']}")
                print()
        
        print("=" * 50)
        print("✅ All tests passed! Your Fortnox connection is working!")
        print()
        return True
        
    except FortnoxRateLimitError as e:
        print()
        print("=" * 50)
        print("⚠️  Test stopped - Rate limit exceeded!")
        print(f"   {str(e)}")
        print()
        print("The Fortnox API has a limit of 300 requests per minute.")
        print("Please wait a few minutes before running tests again.")
        print()
        return False
    except Exception as e:
        print()
        print("=" * 50)
        print("❌ Test failed!")
        print(f"   Error: {str(e)}")
        print()
        print("Common issues:")
        print("  • Invalid Access Token or Client Secret")
        print("  • Network connectivity issues")
        print("  • Fortnox API rate limit exceeded")
        print("  • API permissions not granted")
        print()
        return False


if __name__ == "__main__":
    success = test_fortnox_connection()
    exit(0 if success else 1)
