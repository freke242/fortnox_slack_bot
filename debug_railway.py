#!/usr/bin/env python3
"""Debug script to check Railway deployment"""
import os
import sys

print("=" * 60)
print("Railway Debug Info")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")
print()

print("Files in current directory:")
for item in sorted(os.listdir(".")):
    if not item.startswith('.'):
        full_path = os.path.join(".", item)
        if os.path.isfile(full_path):
            size = os.path.getsize(full_path)
            print(f"  {item:<40} {size:>10} bytes")
        else:
            print(f"  {item:<40} <directory>")

print()
print("Looking for token_manager.py:")
if os.path.exists("token_manager.py"):
    print("  ✅ token_manager.py EXISTS")
    print(f"  Size: {os.path.getsize('token_manager.py')} bytes")
else:
    print("  ❌ token_manager.py NOT FOUND")

print()
print("Trying to import:")
try:
    from token_manager import TokenManager
    print("  ✅ Import successful!")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
