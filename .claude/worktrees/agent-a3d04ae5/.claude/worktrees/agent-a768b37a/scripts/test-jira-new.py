#!/usr/bin/env python3
"""Test Jira connection with new connection."""

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

print(f"Getting Jira connection...")

response = requests.get(
    f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=jira',
    headers={
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': x_replit_token
    }
)

data = response.json()
print(f"Found {len(data.get('items', []))} connections")

if not data.get('items'):
    print("No Jira connection found")
    exit(1)

settings = data['items'][0]['settings']
print(f"Settings keys: {list(settings.keys())}")

access_token = settings.get('access_token')
site_url = settings.get('site_url')

if not access_token:
    oauth = settings.get('oauth', {})
    access_token = oauth.get('credentials', {}).get('access_token')

print(f"Site: {site_url}")
print(f"Token available: {bool(access_token)}")

resp = requests.get(
    f'{site_url}/rest/api/3/myself',
    headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
)

print(f"\nTest /myself: Status {resp.status_code}")
if resp.status_code == 200:
    user = resp.json()
    print(f"Logged in as: {user.get('displayName')} ({user.get('emailAddress')})")
else:
    print(f"Error: {resp.text[:300]}")
