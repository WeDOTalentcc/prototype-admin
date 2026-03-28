#!/usr/bin/env python3
"""
Script para atualizar campos Sprint e Epic das issues no Jira.
"""

import os
import re
import json
import time
import requests
from typing import Dict, List, Optional

def get_jira_credentials():
    """Obtém credenciais do Jira via Replit Connectors."""
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


def get_project_fields(access_token: str, cloud_id: str, project_key: str = "WT") -> Dict:
    """Obtém informações sobre campos customizados do projeto."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/field'
    
    response = requests.get(
        url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
    )
    
    if response.status_code != 200:
        print(f"Erro ao buscar campos: {response.status_code}")
        return {}
    
    fields = response.json()
    field_info = {}
    
    for field in fields:
        name = field.get('name', '').lower()
        if 'sprint' in name or 'epic' in name or 'parent' in name:
            field_info[field['id']] = {
                'name': field.get('name'),
                'type': field.get('schema', {}).get('type'),
                'custom': field.get('custom', False)
            }
            print(f"   Campo encontrado: {field['id']} = {field.get('name')}")
    
    return field_info


def get_board_sprints(access_token: str, cloud_id: str, board_id: int) -> List[dict]:
    """Obtém sprints de um board."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/agile/1.0/board/{board_id}/sprint'
    
    response = requests.get(
        url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
    )
    
    if response.status_code != 200:
        print(f"Erro ao buscar sprints: {response.status_code} - {response.text}")
        return []
    
    return response.json().get('values', [])


def get_boards(access_token: str, cloud_id: str) -> List[dict]:
    """Lista boards disponíveis."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/agile/1.0/board'
    
    response = requests.get(
        url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
    )
    
    if response.status_code != 200:
        print(f"Erro ao buscar boards: {response.status_code}")
        return []
    
    return response.json().get('values', [])


def get_epics(access_token: str, cloud_id: str, project_key: str = "WT") -> List[dict]:
    """Busca épicos do projeto."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search/jql'
    
    response = requests.get(
        url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        },
        params={
            "jql": f'project = {project_key} AND issuetype = Epic ORDER BY key ASC',
            "maxResults": 100,
            "fields": "key,summary"
        }
    )
    
    if response.status_code != 200:
        print(f"Erro ao buscar épicos: {response.status_code}")
        print(response.text)
        return []
    
    return response.json().get('issues', [])


def load_mapping() -> Dict[str, str]:
    """Carrega mapeamento card->issue do resultado anterior."""
    try:
        with open('scripts/jira-full-update-result.json', 'r') as f:
            data = json.load(f)
            return data.get('mapping', {})
    except:
        return {}


def extract_all_cards_from_document(file_path: str) -> Dict[str, dict]:
    """Extrai todos os cards YAML do documento markdown."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    card_pattern = r'### CARD ([A-Z]+-\d+): ([^\n]+)\n+```yaml\n(.*?)```'
    matches = re.findall(card_pattern, content, re.DOTALL)
    
    cards = {}
    for card_id, title, yaml_content in matches:
        cards[card_id] = {
            'id': card_id,
            'title': title.strip(),
            'yaml_content': yaml_content.strip()
        }
    
    return cards


def parse_yaml_field(yaml_content: str, field_name: str) -> Optional[str]:
    """Extrai um campo específico do YAML."""
    pattern = rf'^{field_name}:\s*(.+?)$'
    match = re.search(pattern, yaml_content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def add_labels_to_issue(access_token: str, cloud_id: str, issue_key: str, labels: List[str]) -> bool:
    """Adiciona labels a uma issue."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}'
    
    response = requests.put(
        url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        json={
            'update': {
                'labels': [{'add': label} for label in labels]
            }
        }
    )
    
    return response.status_code == 204


def set_issue_parent(access_token: str, cloud_id: str, issue_key: str, epic_key: str) -> bool:
    """Define o parent (epic) de uma issue."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}'
    
    response = requests.put(
        url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        json={
            'fields': {
                'parent': {'key': epic_key}
            }
        }
    )
    
    if response.status_code == 204:
        return True
    else:
        print(f"      Erro ao definir parent: {response.status_code} - {response.text[:100]}")
        return False


def main():
    print("=" * 60)
    print("ATUALIZAÇÃO DE SPRINT E EPIC NO JIRA")
    print("=" * 60)
    
    # 1. Obter credenciais
    print("\n1. Obtendo credenciais do Jira...")
    try:
        access_token, cloud_id = get_jira_credentials()
        print(f"   ✅ Cloud ID: {cloud_id}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return
    
    # 2. Obter campos do projeto
    print("\n2. Buscando campos customizados...")
    fields = get_project_fields(access_token, cloud_id)
    
    # 3. Buscar boards e sprints
    print("\n3. Buscando boards...")
    boards = get_boards(access_token, cloud_id)
    for board in boards:
        print(f"   Board: {board['id']} - {board['name']}")
    
    # 4. Buscar épicos
    print("\n4. Buscando épicos existentes...")
    epics = get_epics(access_token, cloud_id)
    epic_map = {}
    for epic in epics:
        key = epic['key']
        summary = epic['fields']['summary']
        epic_map[summary.lower()] = key
        print(f"   Épico: {key} - {summary}")
    
    # 5. Carregar mapeamento anterior
    print("\n5. Carregando mapeamento de cards...")
    mapping = load_mapping()
    print(f"   ✅ {len(mapping)} cards mapeados")
    
    # 6. Ler cards do documento
    print("\n6. Lendo cards do documento...")
    cards = extract_all_cards_from_document('docs/lia-mvp-cards-jira.md')
    print(f"   ✅ {len(cards)} cards encontrados")
    
    # 7. Atualizar labels para sprint e epic
    print("\n7. Adicionando labels de Sprint e Epic...")
    success_count = 0
    error_count = 0
    
    for card_id, issue_key in mapping.items():
        card = cards.get(card_id)
        if not card:
            continue
        
        yaml_content = card['yaml_content']
        
        # Extrair sprint
        sprint = parse_yaml_field(yaml_content, 'Sprint')
        epic = parse_yaml_field(yaml_content, 'Epic')
        
        labels_to_add = []
        
        if sprint:
            sprint_label = f"sprint-{sprint}"
            labels_to_add.append(sprint_label)
        
        if epic:
            epic_label = epic.lower().replace('_', '-')
            labels_to_add.append(epic_label)
        
        if labels_to_add:
            result = add_labels_to_issue(access_token, cloud_id, issue_key, labels_to_add)
            if result:
                success_count += 1
                print(f"   ✅ {issue_key} ({card_id}) - Labels: {', '.join(labels_to_add)}")
            else:
                error_count += 1
                print(f"   ❌ {issue_key} ({card_id}) - Erro ao adicionar labels")
        
        time.sleep(0.2)  # Rate limiting
    
    # 8. Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Cards processados: {len(mapping)}")
    print(f"Labels adicionadas: {success_count}")
    print(f"Erros: {error_count}")


if __name__ == '__main__':
    main()
