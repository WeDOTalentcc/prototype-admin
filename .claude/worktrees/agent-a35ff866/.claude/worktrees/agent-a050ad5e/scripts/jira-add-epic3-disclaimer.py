#!/usr/bin/env python3
"""
Script para adicionar disclaimer no INÍCIO dos cards do Épico 3 no Jira.
Informa que atualizações de UI foram feitas no protótipo Replit com base
nas sugestões da reunião com André.
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


def build_disclaimer_adf():
    """Build ADF nodes for the disclaimer panel at the very beginning."""
    return [
        {
            "type": "panel",
            "attrs": {"panelType": "warning"},
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 3},
                    "content": [
                        {"type": "text", "text": "⚠️ DISCLAIMER — Protótipo Replit em Atualização"}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "O protótipo Replit deste card ainda não foi atualizado com as sugestões da reunião com o André. "
                        },
                        {
                            "type": "text",
                            "text": "As melhorias de UI serão implementadas no protótipo Replit para servir como referência visual atualizada para a implementação em Vue/Nuxt/Vuetify.",
                            "marks": [{"type": "strong"}]
                        }
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Aguarde a atualização do protótipo antes de usar os componentes como referência final de UI."
                        }
                    ]
                }
            ]
        },
        {
            "type": "rule"
        }
    ]


def get_issue_description(access_token, cloud_id, issue_key):
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}?fields=description,summary'
    resp = requests.get(url, headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    })
    
    if resp.status_code != 200:
        return None, None
    
    data = resp.json()
    return data.get('fields', {}).get('description'), data.get('fields', {}).get('summary', '')


def has_old_disclaimer(description):
    if not description:
        return False
    desc_str = json.dumps(description)
    return 'DISCLAIMER' in desc_str and 'Prot\u00f3tipo Replit' in desc_str


def has_new_disclaimer(description):
    if not description:
        return False
    desc_str = json.dumps(description)
    return 'em Atualiza' in desc_str and 'ainda n\u00e3o foi atualizado' in desc_str


def remove_old_disclaimer(description):
    if not description or not description.get('content'):
        return description
    new_content = []
    skip_next_rule = False
    for node in description['content']:
        if node.get('type') == 'panel' and 'DISCLAIMER' in json.dumps(node):
            skip_next_rule = True
            continue
        if skip_next_rule and node.get('type') == 'rule':
            skip_next_rule = False
            continue
        skip_next_rule = False
        new_content.append(node)
    return {
        "version": 1,
        "type": "doc",
        "content": new_content
    }


def update_issue_description(access_token, cloud_id, issue_key, new_description):
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


def main():
    dry_run = '--dry-run' in sys.argv
    
    print("=" * 60)
    print("JIRA EPIC 3 DISCLAIMER UPDATER")
    print("=" * 60)
    
    if dry_run:
        print("*** DRY RUN MODE - No changes will be made ***\n")
    
    with open('scripts/card-to-jira-key.json') as f:
        card_to_jira = json.load(f)
    
    epic3_cards = {k: v for k, v in card_to_jira.items() if k.startswith('MAP-')}
    
    print(f"Cards do Épico 3 encontrados: {len(epic3_cards)}")
    for card_id, jira_key in sorted(epic3_cards.items()):
        print(f"  {card_id} -> {jira_key}")
    
    access_token, cloud_id = get_jira_credentials()
    print(f"\nConectado ao Jira (cloud_id: {cloud_id[:8]}...)")
    
    results = {
        'updated': [],
        'already_has_disclaimer': [],
        'errors': []
    }
    
    disclaimer_nodes = build_disclaimer_adf()
    
    print("\n--- Adicionando disclaimer ---")
    
    for card_id, jira_key in sorted(epic3_cards.items()):
        try:
            desc, summary = get_issue_description(access_token, cloud_id, jira_key)
            
            if has_new_disclaimer(desc):
                results['already_has_disclaimer'].append({'cardId': card_id, 'jiraKey': jira_key})
                print(f"  SKIP {card_id} ({jira_key}): já tem disclaimer correto")
                continue
            
            if has_old_disclaimer(desc):
                desc = remove_old_disclaimer(desc)
                print(f"  DEL  {card_id} ({jira_key}): removeu disclaimer antigo")
            
            if desc and desc.get('content'):
                new_desc = {
                    "version": 1,
                    "type": "doc",
                    "content": disclaimer_nodes + desc['content']
                }
            else:
                new_desc = {
                    "version": 1,
                    "type": "doc",
                    "content": disclaimer_nodes
                }
            
            if dry_run:
                print(f"  DRY {card_id} ({jira_key}): {summary[:60]}")
                results['updated'].append({'cardId': card_id, 'jiraKey': jira_key, 'summary': summary})
            else:
                status, text = update_issue_description(access_token, cloud_id, jira_key, new_desc)
                
                if status in (200, 204):
                    results['updated'].append({'cardId': card_id, 'jiraKey': jira_key, 'summary': summary})
                    print(f"  OK  {card_id} ({jira_key}): {summary[:60]}")
                else:
                    results['errors'].append({'cardId': card_id, 'jiraKey': jira_key, 'status': status, 'error': text[:200]})
                    print(f"  ERR {card_id} ({jira_key}): {status} - {text[:100]}")
                
                time.sleep(0.3)
        
        except Exception as e:
            results['errors'].append({'cardId': card_id, 'jiraKey': jira_key, 'error': str(e)})
            print(f"  ERR {card_id} ({jira_key}): {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("RESULTADO")
    print("=" * 60)
    print(f"Atualizados:        {len(results['updated'])}")
    print(f"Já tinha disclaimer:{len(results['already_has_disclaimer'])}")
    print(f"Erros:              {len(results['errors'])}")
    
    if results['errors']:
        print(f"\nErros:")
        for e in results['errors']:
            print(f"  {e['cardId']}: {e.get('error', '')[:100]}")
    
    with open('scripts/jira-epic3-disclaimer-result.json', 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultados salvos em scripts/jira-epic3-disclaimer-result.json")


if __name__ == '__main__':
    main()
