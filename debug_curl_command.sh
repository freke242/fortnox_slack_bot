curl -X POST https://apps.fortnox.se/oauth-v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic d2ViSmJUdUtnT3Q1OkpvMnZsWEQ2NlY=" \
  -d "grant_type=authorization_code" \
  -d "code=c72dbafb-290c-4d90-bff6-83b96eccb05a" \
  -d "redirect_uri=http://localhost:33140/callback"