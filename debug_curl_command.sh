curl -X POST https://apps.fortnox.se/oauth-v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic d2ViSmJUdUtnT3Q1OkpvMnZsWEQ2NlY=" \
  -d "grant_type=authorization_code" \
  -d "code=5ef70ae1-a44f-4ca1-99eb-da47f408f929" \
  -d "redirect_uri=http://localhost:33140/callback"