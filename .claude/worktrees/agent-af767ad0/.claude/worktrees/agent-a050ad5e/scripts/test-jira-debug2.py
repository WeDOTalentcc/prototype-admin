#!/usr/bin/env python3
"""Debug Jira connection - check OAuth settings."""

import os
import json
import requests
from datetime import datetime

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

if 'items' in data and len(data['items']) > 0:
    settings = data['items'][0].get('settings', {})
    oauth = settings.get('oauth', {})
    
    print("OAuth settings:")
    print(json.dumps(oauth, indent=2, default=str)[:2000])
