#!/usr/bin/env python3
"""Debug Jira connection."""

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
    print("No Replit token available")
    exit(1)

print(f"Hostname: {hostname}")
print(f"Token type: {'repl' if repl_identity else 'depl'}")

response = requests.get(
    f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=jira',
    headers={
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': x_replit_token
    }
)

print(f"\nStatus: {response.status_code}")
data = response.json()

if 'items' in data and len(data['items']) > 0:
    settings = data['items'][0].get('settings', {})
    print(f"\nSettings keys: {list(settings.keys())}")
    
    if 'expires_at' in settings:
        print(f"Expires at: {settings['expires_at']}")
    
    if 'access_token' in settings:
        token = settings['access_token']
        print(f"Token (last 20 chars): ...{token[-20:]}")
    
    if 'site_url' in settings:
        print(f"Site URL: {settings['site_url']}")
else:
    print(f"\nFull response: {json.dumps(data, indent=2)[:1000]}")
