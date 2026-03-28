#!/usr/bin/env python3
"""Test Jira with OAuth token from credentials."""

import os
import requests

hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
repl_identity = os.environ.get('REPL_IDENTITY')
web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')

if repl_identity:
    x_replit_token = f'repl {repl_identity}'
elif web_repl_renewal:
    x_replit_token = f'depl {web_repl_renewal}'
else:
    exit(1)

response = requests.get(
    f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=jira',
    headers={
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': x_replit_token
    }
)

data = response.json()
settings = data['items'][0]['settings']

token = settings.get('oauth', {}).get('credentials', {}).get('access_token')
site_url = settings.get('site_url')

print(f"Site: {site_url}")
print(f"Token from oauth.credentials")

url = f'{site_url}/rest/api/3/myself'
resp = requests.get(
    url,
    headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
)

print(f"\nTest /myself endpoint:")
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")
