curl -X POST https://apps.fortnox.se/oauth-v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic d2ViSmJUdUtnT3Q1OkpvMnZsWEQ2NlY=" \
  -d "grant_type=authorization_code" \
  -d "code=c3d7aeb4-8f11-494b-b997-9c7e1d68675b" \
  -d "redirect_uri=http://localhost:33140/callback"