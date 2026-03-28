#!/usr/bin/env python3
"""Test Jira connection - get cloud ID and use correct API."""

import os
import json
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

access_token = settings.get('access_token')
site_url = settings.get('site_url')

if not access_token:
    access_token = settings.get('oauth', {}).get('credentials', {}).get('access_token')

print(f"Access token: ...{access_token[-30:]}")
print(f"Site URL: {site_url}")

print("\n1. Getting accessible resources (cloud IDs)...")
resp = requests.get(
    'https://api.atlassian.com/oauth/token/accessible-resources',
    headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
)

print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    resources = resp.json()
    print(f"Resources: {json.dumps(resources, indent=2)}")
    
    if resources:
        cloud_id = resources[0]['id']
        print(f"\nCloud ID: {cloud_id}")
        
        print("\n2. Testing API with cloud ID...")
        api_resp = requests.get(
            f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            }
        )
        print(f"Status: {api_resp.status_code}")
        if api_resp.status_code == 200:
            user = api_resp.json()
            print(f"User: {user.get('displayName')}")
        else:
            print(f"Error: {api_resp.text[:300]}")
else:
    print(f"Error: {resp.text[:500]}")
