#!/usr/bin/env python3
"""
Complete setup checker
Validates everything needed to run the Fortnox Slack Bot
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8+"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (need 3.8+)")
        return False

def check_virtual_env():
    """Check if running in a virtual environment"""
    print("🏠 Checking virtual environment...")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("   ✅ Running in virtual environment")
        return True
    else:
        print("   ⚠️  Not in a virtual environment (recommended)")
        return True  # Warning, not error

def check_dependencies():
    """Check if all dependencies are installed"""
    print("📦 Checking dependencies...")
    try:
        import slack_bolt
        import dotenv
        import requests
        print("   ✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e.name}")
        print("      Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    print("🔧 Checking .env file...")
    if Path(".env").exists():
        print("   ✅ .env file exists")
        return True
    else:
        print("   ❌ .env file not found")
        print("      Run: cp .env.example .env")
        print("      Then edit .env with your credentials")
        return False

def check_env_variables():
    """Check if environment variables are set"""
    print("🔑 Checking environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    
    required = [
        "SLACK_BOT_TOKEN",
        "SLACK_SIGNING_SECRET", 
        "SLACK_APP_TOKEN",
        "FORTNOX_ACCESS_TOKEN",
        "FORTNOX_CLIENT_SECRET"
    ]
    
    missing = [var for var in required if not os.getenv(var)]
    
    if not missing:
        print(f"   ✅ All {len(required)} variables set")
        return True
    else:
        print(f"   ❌ Missing: {', '.join(missing)}")
        return False

def check_file_permissions():
    """Check if .env has secure permissions"""
    print("🔒 Checking file permissions...")
    env_file = Path(".env")
    if not env_file.exists():
        print("   ⏭️  Skipped (.env not found)")
        return True
    
    # Check permissions on Unix-like systems
    if os.name != 'nt':  # Not Windows
        stat_info = env_file.stat()
        mode = stat_info.st_mode & 0o777
        if mode == 0o600 or mode == 0o644:
            print(f"   ✅ Secure permissions ({oct(mode)})")
            return True
        else:
            print(f"   ⚠️  Permissions {oct(mode)} (recommend 600)")
            print("      Run: chmod 600 .env")
            return True  # Warning, not error
    else:
        print("   ℹ️  Permission check skipped (Windows)")
        return True

def check_network():
    """Check network connectivity"""
    print("🌐 Checking network connectivity...")
    try:
        import requests
        requests.get("https://api.slack.com", timeout=5)
        print("   ✅ Can reach Slack API")
        return True
    except Exception as e:
        print(f"   ⚠️  Network check failed: {e}")
        return True  # Warning, not error

def run_all_checks():
    """Run all checks and report results"""
    print("=" * 60)
    print("🔍 Fortnox Slack Bot - Setup Checker")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_env),
        ("Dependencies", check_dependencies),
        (".env File", check_env_file),
        ("Environment Variables", check_env_variables),
        ("File Permissions", check_file_permissions),
        ("Network", check_network),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            results.append(check_func())
        except Exception as e:
            print(f"   ❌ Check failed: {e}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for (name, _), result in zip(checks, results):
        icon = "✅" if result else "❌"
        print(f"{icon} {name}")
    
    print()
    print(f"Result: {passed}/{total} checks passed")
    print()
    
    if all(results):
        print("🎉 All checks passed! You're ready to run the bot.")
        print()
        print("Start the bot with: python app.py")
        print()
        return True
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        print("Quick fixes:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Copy environment file: cp .env.example .env")
        print("  3. Edit .env with your credentials")
        print("  4. Validate config: python validate_config.py")
        print()
        return False

if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
