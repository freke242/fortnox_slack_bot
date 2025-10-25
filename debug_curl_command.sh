curl -X POST https://apps.fortnox.se/oauth-v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic d2ViSmJUdUtnT3Q1OkpvMnZsWEQ2NlY=" \
  -d "grant_type=authorization_code" \
  -d "code=61425c6b-d709-40cc-90c3-9f93013c5bcb" \
  -d "redirect_uri=http://localhost:33140/callback"