#!/usr/bin/env python3
"""
Script para extrair descrições completas dos cards YAML e atualizar no Jira.
"""

import os
import re
import json
import time
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
    
    resources = resp.json()
    cloud_id = resources[0]['id']
    
    return access_token, cloud_id


def extract_yaml_cards(file_path):
    """Extrai blocos YAML de cards do arquivo markdown."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    yaml_pattern = r'### CARD (VAG-\d+):.*?\n\n```yaml\n(.*?)```'
    matches = re.findall(yaml_pattern, content, re.DOTALL)
    
    cards = {}
    for card_id, yaml_content in matches:
        cards[card_id] = yaml_content.strip()
    
    return cards


def yaml_to_jira_description(card_id, yaml_content):
    """Converte conteúdo YAML em descrição formatada para Jira."""
    lines = yaml_content.split('\n')
    
    sections = []
    current_section = None
    current_content = []
    indent_level = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            if current_section and current_content:
                sections.append((current_section, '\n'.join(current_content)))
            
            parts = line.split(':', 1)
            current_section = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ''
            
            if value and value != '|':
                current_content = [value]
            else:
                current_content = []
        else:
            if stripped.startswith('- '):
                current_content.append(f"• {stripped[2:]}")
            else:
                current_content.append(stripped)
    
    if current_section and current_content:
        sections.append((current_section, '\n'.join(current_content)))
    
    formatted_parts = []
    formatted_parts.append(f"*Card ID:* {card_id}\n")
    
    for section, content in sections:
        if content:
            formatted_parts.append(f"*{section}:*\n{content}\n")
    
    return '\n'.join(formatted_parts)


def create_adf_description(text):
    """Cria descrição em formato ADF (Atlassian Document Format)."""
    paragraphs = text.split('\n\n')
    content = []
    
    for para in paragraphs:
        if para.strip():
            lines = para.split('\n')
            para_content = []
            
            for line in lines:
                if line.strip():
                    if line.startswith('*') and line.endswith('*'):
                        para_content.append({
                            'type': 'text',
                            'text': line.strip('*'),
                            'marks': [{'type': 'strong'}]
                        })
                    elif '*' in line:
                        parts = re.split(r'(\*[^*]+\*)', line)
                        for part in parts:
                            if part.startswith('*') and part.endswith('*'):
                                para_content.append({
                                    'type': 'text',
                                    'text': part.strip('*'),
                                    'marks': [{'type': 'strong'}]
                                })
                            elif part:
                                para_content.append({'type': 'text', 'text': part})
                    else:
                        para_content.append({'type': 'text', 'text': line})
                    
                    para_content.append({'type': 'text', 'text': '\n'})
            
            if para_content:
                if para_content[-1]['text'] == '\n':
                    para_content.pop()
                    
                content.append({
                    'type': 'paragraph',
                    'content': para_content
                })
    
    return {
        'type': 'doc',
        'version': 1,
        'content': content
    }


def update_jira_issue(access_token, cloud_id, issue_key, description_text):
    """Atualiza a descrição de uma issue no Jira."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}'
    
    adf_description = create_adf_description(description_text)
    
    try:
        response = requests.put(
            url,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json={
                'fields': {
                    'description': adf_description
                }
            }
        )
        
        if response.status_code == 204:
            return {'success': True}
        else:
            try:
                error = response.json()
            except:
                error = {'status': response.status_code, 'text': response.text[:200]}
            return {'success': False, 'error': error}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    print("Obtendo credenciais do Jira...")
    access_token, cloud_id = get_jira_credentials()
    print(f"Cloud ID: {cloud_id}")
    
    print("\nExtraindo cards YAML do documento...")
    cards = extract_yaml_cards('docs/gestao-vagas-visao-geral-cards-jira.md')
    print(f"Encontrados {len(cards)} cards com especificações YAML")
    
    print("\nCarregando mapeamento de cards criados...")
    with open('scripts/jira-creation-result.json', 'r') as f:
        creation_result = json.load(f)
    
    id_to_key = {item['id']: item['key'] for item in creation_result['created']}
    print(f"Mapeamento: {len(id_to_key)} cards")
    
    updated = []
    failed = []
    skipped = []
    
    print(f"\nAtualizando descrições no Jira...")
    print("-" * 60)
    
    for card_id, yaml_content in cards.items():
        if card_id not in id_to_key:
            skipped.append(card_id)
            continue
        
        issue_key = id_to_key[card_id]
        description = yaml_to_jira_description(card_id, yaml_content)
        
        result = update_jira_issue(access_token, cloud_id, issue_key, description)
        
        if result['success']:
            updated.append({'id': card_id, 'key': issue_key})
            print(f"✓ {issue_key} ({card_id}) atualizado")
        else:
            failed.append({'id': card_id, 'key': issue_key, 'error': result['error']})
            print(f"✗ {issue_key} ({card_id}): {result['error']}")
        
        time.sleep(0.2)
    
    print("\n" + "=" * 60)
    print(f"RESULTADO: {len(updated)} atualizados, {len(failed)} falhas, {len(skipped)} ignorados")
    
    if failed:
        print("\nCards com falha:")
        for f in failed[:10]:
            print(f"  - {f['key']}: {f['error']}")
    
    with open('scripts/jira-update-result.json', 'w') as f:
        json.dump({'updated': updated, 'failed': failed, 'skipped': skipped}, f, indent=2)
    
    print(f"\nResultado salvo em scripts/jira-update-result.json")


if __name__ == "__main__":
    main()
