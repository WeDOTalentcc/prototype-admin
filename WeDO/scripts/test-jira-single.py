#!/usr/bin/env python3
"""Teste de criação de um único card no Jira."""

import os
import requests

def get_jira_credentials():
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
    
    if repl_identity:
        x_replit_token = f'repl {repl_identity}'
    elif web_repl_renewal:
        x_replit_token = f'depl {web_repl_renewal}'
    else:
        raise ValueError('No Replit token available')
    
    response = requests.get(
        f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=jira',
        headers={
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
    )
    
    data = response.json()
    connection = data.get('items', [{}])[0]
    settings = connection.get('settings', {})
    
    access_token = settings.get('access_token') or settings.get('oauth', {}).get('credentials', {}).get('access_token')
    site_url = settings.get('site_url')
    
    return access_token, site_url

print("Obtendo credenciais...")
token, site = get_jira_credentials()
print(f"Site: {site}")

url = f'{site}/rest/api/3/issue'
fields = {
    'project': {'key': 'WT'},
    'summary': '[TEST] Card de Teste - DELETAR',
    'description': {
        'type': 'doc',
        'version': 1,
        'content': [
            {'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Teste de criacao via API'}]}
        ]
    },
    'issuetype': {'name': 'Task'},
    'labels': ['TEST'],
}

print(f"\nCriando issue em {url}...")
response = requests.post(
    url,
    headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    },
    json={'fields': fields}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500] if response.text else 'Empty'}")
