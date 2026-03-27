#!/usr/bin/env python3
"""
Script para adicionar seção de 'Arquivos de Referência (Protótipo Replit)' 
no INÍCIO da descrição de cada card no Jira.
"""

import os
import json
import time
import requests
import sys

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
    settings = data['items'][0]['settings']
    
    access_token = settings.get('access_token')
    if not access_token:
        access_token = settings.get('oauth', {}).get('credentials', {}).get('access_token')
    
    resp = requests.get(
        'https://api.atlassian.com/oauth/token/accessible-resources',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
    )
    
    if resp.status_code != 200:
        raise ValueError(f'Failed to get cloud ID: {resp.status_code} {resp.text}')
    
    resources = resp.json()
    cloud_id = resources[0]['id']
    
    return access_token, cloud_id


def build_refs_adf_block(refs):
    """Build ADF nodes for the file references section."""
    nodes = []
    
    nodes.append({
        "type": "heading",
        "attrs": {"level": 3},
        "content": [{"type": "text", "text": "📁 Arquivos de Referência (Protótipo Replit)"}]
    })
    
    list_items = []
    for ref in refs:
        list_items.append({
            "type": "listItem",
            "content": [{
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": ref['filename'] + ": ", "marks": [{"type": "strong"}]},
                    {
                        "type": "text",
                        "text": ref['url'],
                        "marks": [{"type": "link", "attrs": {"href": ref['url']}}]
                    }
                ]
            }]
        })
    
    nodes.append({
        "type": "bulletList",
        "content": list_items
    })
    
    nodes.append({
        "type": "rule"
    })
    
    return nodes


def get_issue_description(access_token, cloud_id, issue_key):
    """Get current issue description (ADF format)."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}?fields=description'
    resp = requests.get(url, headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    })
    
    if resp.status_code != 200:
        return None
    
    data = resp.json()
    return data.get('fields', {}).get('description')


def has_refs_section(description):
    """Check if description already has the refs section."""
    if not description:
        return False
    
    desc_str = json.dumps(description)
    return 'Arquivos de Refer' in desc_str or 'Prot\u00f3tipo Replit' in desc_str


def update_issue_description(access_token, cloud_id, issue_key, new_description):
    """Update issue description."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}'
    resp = requests.put(url, 
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        json={
            "fields": {
                "description": new_description
            }
        }
    )
    return resp.status_code, resp.text


def search_issues_by_summary(access_token, cloud_id, search_text, project='WT'):
    """Search for issues by summary text using new Jira search API."""
    jql = f'project = {project} AND summary ~ "\\\"{search_text}\\\""'
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search/jql'
    resp = requests.get(url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        },
        params={
            'jql': jql,
            'fields': 'summary',
            'maxResults': 5
        }
    )
    
    if resp.status_code != 200:
        return []
    
    data = resp.json()
    return [(i['key'], i['fields']['summary']) for i in data.get('issues', [])]


def main():
    dry_run = '--dry-run' in sys.argv
    search_missing = '--search-missing' in sys.argv
    
    print("=" * 60)
    print("JIRA FILE REFERENCES UPDATER")
    print("=" * 60)
    
    if dry_run:
        print("*** DRY RUN MODE - No changes will be made ***\n")
    
    with open('scripts/card-refs-data.json') as f:
        card_refs = json.load(f)
    
    with open('scripts/card-to-jira-key.json') as f:
        card_to_jira = json.load(f)
    
    print(f"Cards with references: {len(card_refs)}")
    print(f"Cards with Jira key mapping: {len(card_to_jira)}")
    
    access_token, cloud_id = get_jira_credentials()
    print(f"Connected to Jira (cloud_id: {cloud_id[:8]}...)")
    
    results = {
        'updated': [],
        'already_has_refs': [],
        'no_jira_key': [],
        'errors': [],
        'found_by_search': []
    }
    
    if search_missing:
        print("\n--- Searching for unmapped cards by title ---")
        for card_id, card_data in card_refs.items():
            if card_id in card_to_jira:
                continue
            
            matches = search_issues_by_summary(access_token, cloud_id, card_id)
            if matches:
                jira_key = matches[0][0]
                card_to_jira[card_id] = jira_key
                results['found_by_search'].append({'cardId': card_id, 'jiraKey': jira_key})
                print(f"  Found {card_id} -> {jira_key}")
            else:
                title_short = card_data['title'][:30]
                matches2 = search_issues_by_summary(access_token, cloud_id, title_short)
                if matches2:
                    jira_key = matches2[0][0]
                    card_to_jira[card_id] = jira_key
                    results['found_by_search'].append({'cardId': card_id, 'jiraKey': jira_key})
                    print(f"  Found {card_id} by title -> {jira_key}")
            
            time.sleep(0.3)
        
        with open('scripts/card-to-jira-key.json', 'w') as f:
            json.dump(card_to_jira, f, indent=2)
        print(f"  Found {len(results['found_by_search'])} additional mappings")
    
    print("\n--- Updating cards ---")
    
    for card_id, card_data in sorted(card_refs.items()):
        jira_key = card_to_jira.get(card_id)
        
        if not jira_key:
            results['no_jira_key'].append(card_id)
            continue
        
        try:
            desc = get_issue_description(access_token, cloud_id, jira_key)
            
            if has_refs_section(desc):
                results['already_has_refs'].append({'cardId': card_id, 'jiraKey': jira_key})
                print(f"  SKIP {card_id} ({jira_key}): already has refs")
                continue
            
            refs_nodes = build_refs_adf_block(card_data['refs'])
            
            if desc and desc.get('content'):
                new_desc = {
                    "version": 1,
                    "type": "doc",
                    "content": refs_nodes + desc['content']
                }
            else:
                new_desc = {
                    "version": 1,
                    "type": "doc",
                    "content": refs_nodes
                }
            
            if dry_run:
                print(f"  DRY {card_id} ({jira_key}): would add {len(card_data['refs'])} refs")
                results['updated'].append({'cardId': card_id, 'jiraKey': jira_key, 'refsCount': len(card_data['refs'])})
            else:
                status, text = update_issue_description(access_token, cloud_id, jira_key, new_desc)
                
                if status in (200, 204):
                    results['updated'].append({'cardId': card_id, 'jiraKey': jira_key, 'refsCount': len(card_data['refs'])})
                    print(f"  OK {card_id} ({jira_key}): added {len(card_data['refs'])} refs")
                else:
                    results['errors'].append({'cardId': card_id, 'jiraKey': jira_key, 'status': status, 'error': text[:200]})
                    print(f"  ERR {card_id} ({jira_key}): {status} - {text[:100]}")
                
                time.sleep(0.2)
        
        except Exception as e:
            results['errors'].append({'cardId': card_id, 'jiraKey': jira_key, 'error': str(e)})
            print(f"  ERR {card_id} ({jira_key}): {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Updated:           {len(results['updated'])}")
    print(f"Already had refs:  {len(results['already_has_refs'])}")
    print(f"No Jira key:       {len(results['no_jira_key'])}")
    print(f"Found by search:   {len(results['found_by_search'])}")
    print(f"Errors:            {len(results['errors'])}")
    
    if results['no_jira_key']:
        print(f"\nCards without Jira key:")
        for c in results['no_jira_key']:
            print(f"  {c}")
    
    if results['errors']:
        print(f"\nErrors:")
        for e in results['errors']:
            print(f"  {e['cardId']}: {e.get('error', '')[:100]}")
    
    with open('scripts/jira-refs-update-result.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to scripts/jira-refs-update-result.json")


if __name__ == '__main__':
    main()
