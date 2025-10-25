curl -X POST https://apps.fortnox.se/oauth-v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic d2ViSmJUdUtnT3Q1OkpvMnZsWEQ2NlY=" \
  -d "grant_type=authorization_code" \
  -d "code=00554ad0-b3eb-435f-83b7-4c78d9b5e138" \
  -d "redirect_uri=http://localhost:33140/callback"