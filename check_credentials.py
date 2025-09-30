#!/usr/bin/env python3
"""
Check for issues in credentials (whitespace, quotes, etc.)
"""
import os
from dotenv import load_dotenv

load_dotenv()

def check_credential(name):
    """Check a credential for common issues"""
    value = os.getenv(name)
    if not value:
        print(f"❌ {name}: NOT SET")
        return False
    
    print(f"\n🔍 {name}:")
    print(f"   Length: {len(value)}")
    print(f"   First 10 chars: {repr(value[:10])}")
    print(f"   Last 10 chars: {repr(value[-10:])}")
    
    issues = []
    
    # Check for whitespace
    if value != value.strip():
        issues.append("Has leading/trailing whitespace")
    
    # Check for quotes
    if value.startswith('"') or value.startswith("'"):
        issues.append("Starts with quote")
    if value.endswith('"') or value.endswith("'"):
        issues.append("Ends with quote")
    
    # Check for newlines
    if '\n' in value or '\r' in value:
        issues.append("Contains newline characters")
    
    # Check for tabs
    if '\t' in value:
        issues.append("Contains tab characters")
    
    if issues:
        print(f"   ⚠️  Issues found:")
        for issue in issues:
            print(f"      - {issue}")
        return False
    else:
        print(f"   ✅ Looks clean")
        return True

print("=" * 60)
print("🔍 Credential Checker")
print("=" * 60)

all_good = True
all_good &= check_credential("FORTNOX_CLIENT_ID")
all_good &= check_credential("FORTNOX_CLIENT_SECRET")

print("\n" + "=" * 60)
if all_good:
    print("✅ All credentials look clean")
else:
    print("⚠️  Some credentials have issues - clean them up!")
print("=" * 60)
