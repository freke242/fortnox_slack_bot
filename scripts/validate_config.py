"""
Configuration validator
Checks if all required environment variables are set correctly
"""
import os
from dotenv import load_dotenv
import sys

def validate_config():
    """Validate all required environment variables"""
    
    print("🔍 Validating configuration...")
    print("=" * 50)
    print()
    
    # Load environment variables
    load_dotenv()
    
    # Define required variables with validation rules
    required_vars = {
        "SLACK_BOT_TOKEN": {
            "prefix": "xoxb-",
            "description": "Slack Bot User OAuth Token"
        },
        "SLACK_SIGNING_SECRET": {
            "min_length": 32,
            "description": "Slack App Signing Secret"
        },
        "SLACK_APP_TOKEN": {
            "prefix": "xapp-",
            "description": "Slack App-Level Token (for Socket Mode)"
        },
        "FORTNOX_ACCESS_TOKEN": {
            "min_length": 10,
            "description": "Fortnox API Access Token"
        },
        "FORTNOX_CLIENT_SECRET": {
            "min_length": 10,
            "description": "Fortnox API Client Secret"
        }
    }
    
    errors = []
    warnings = []
    success_count = 0
    
    # Check each required variable
    for var_name, rules in required_vars.items():
        value = os.getenv(var_name)
        
        if not value:
            errors.append(f"❌ {var_name} is not set")
            print(f"❌ {var_name}")
            print(f"   Description: {rules['description']}")
            print()
            continue
        
        # Check prefix if specified
        if "prefix" in rules and not value.startswith(rules["prefix"]):
            warnings.append(
                f"⚠️  {var_name} should start with '{rules['prefix']}'"
            )
            print(f"⚠️  {var_name} - Warning: Should start with '{rules['prefix']}'")
            print(f"   Current value starts with: {value[:10]}...")
            print()
        
        # Check minimum length if specified
        elif "min_length" in rules and len(value) < rules["min_length"]:
            warnings.append(
                f"⚠️  {var_name} seems too short (length: {len(value)})"
            )
            print(f"⚠️  {var_name} - Warning: Seems too short")
            print()
        
        else:
            success_count += 1
            # Show partial value for verification
            if len(value) > 20:
                display_value = f"{value[:8]}...{value[-4:]}"
            else:
                display_value = f"{value[:8]}..."
            
            print(f"✅ {var_name}")
            print(f"   Value: {display_value}")
            print()
    
    # Summary
    print("=" * 50)
    print("Summary:")
    print(f"  ✅ Valid: {success_count}/{len(required_vars)}")
    
    if warnings:
        print(f"  ⚠️  Warnings: {len(warnings)}")
        for warning in warnings:
            print(f"     {warning}")
    
    if errors:
        print(f"  ❌ Errors: {len(errors)}")
        for error in errors:
            print(f"     {error}")
        print()
        print("❌ Configuration validation failed!")
        print()
        print("Please check your .env file and ensure all required")
        print("environment variables are set correctly.")
        print()
        print("Refer to .env.example for the required format.")
        return False
    
    print()
    if warnings:
        print("⚠️  Configuration is set but has warnings.")
        print("   The bot might not work correctly.")
        print()
        return True
    else:
        print("✅ Configuration is valid!")
        print("   You're ready to run the bot.")
        print()
        return True


if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)
