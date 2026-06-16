#!/usr/bin/env python3
"""
Script para atualizar os cards do Jira do Menu Configurações.
Documento: docs/configuracoes-admin-cards-jira.md
Label Jira: menu config
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


def parse_yaml_content(yaml_content: str) -> dict:
    """Parse simples do conteúdo YAML para extrair campos."""
    result = {}
    current_key = None
    current_value = []
    
    for line in yaml_content.split('\n'):
        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            if current_key:
                result[current_key] = '\n'.join(current_value).strip()
            
            parts = line.split(':', 1)
            current_key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ''
            
            if value == '|':
                current_value = []
            elif value:
                current_value = [value]
            else:
                current_value = []
        else:
            if current_key:
                current_value.append(line)
    
    if current_key:
        result[current_key] = '\n'.join(current_value).strip()
    
    return result


def yaml_to_jira_adf(card_id: str, yaml_content: str) -> dict:
    """Converte conteúdo YAML completo para formato ADF do Jira."""
    parsed = parse_yaml_content(yaml_content)
    
    content = []
    
    content.append({
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": f"Card {card_id}", "marks": [{"type": "strong"}]}]
    })
    
    field_order = [
        ("Descricao", "Descrição"),
        ("Historia de Usuario", "História de Usuário"),
        ("Regras de Negocio", "Regras de Negócio"),
        ("Requisitos Tecnicos", "Requisitos Técnicos"),
        ("Design & Componentes", "Design & Componentes"),
        ("Comportamento de UI", "Comportamento de UI"),
        ("Comportamento de API", "Comportamento de API"),
        ("Integracoes Externas", "Integrações Externas"),
        ("Referencias de Design", "Referências de Design"),
        ("DoD", "Definition of Done"),
        ("DoD (Definition of Done)", "Definition of Done"),
        ("Criterios de Aceitacao", "Critérios de Aceitação"),
        ("Dependencias", "Dependências")
    ]
    
    processed_fields = set()
    
    for yaml_key, display_name in field_order:
        if yaml_key in parsed and parsed[yaml_key] and display_name not in processed_fields:
            value = parsed[yaml_key]
            processed_fields.add(display_name)
            
            content.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": display_name}]
            })
            
            lines = value.split('\n')
            
            if any(line.strip().startswith('- ') or line.strip().startswith('• ') for line in lines):
                list_items = []
                current_para = []
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('- ') or stripped.startswith('• '):
                        if current_para:
                            content.append({
                                "type": "paragraph",
                                "content": [{"type": "text", "text": ' '.join(current_para)}]
                            })
                            current_para = []
                        
                        list_items.append({
                            "type": "listItem",
                            "content": [{
                                "type": "paragraph",
                                "content": [{"type": "text", "text": stripped.lstrip('-• ').strip()}]
                            }]
                        })
                    elif stripped and not stripped.endswith(':'):
                        current_para.append(stripped)
                
                if current_para:
                    content.append({
                        "type": "paragraph",
                        "content": [{"type": "text", "text": ' '.join(current_para)}]
                    })
                
                if list_items:
                    content.append({
                        "type": "bulletList",
                        "content": list_items
                    })
            else:
                text_content = ' '.join(line.strip() for line in lines if line.strip())
                if text_content:
                    content.append({
                        "type": "paragraph",
                        "content": [{"type": "text", "text": text_content}]
                    })
    
    tech_info = []
    for key in ["Tipo", "Sprint", "Pontos", "Prioridade", "Epic", "Status"]:
        if key in parsed:
            tech_info.append(f"{key}: {parsed[key]}")
    
    if tech_info:
        content.append({
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "Informações do Card"}]
        })
        content.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": ' | '.join(tech_info)}]
        })
    
    return {
        "type": "doc",
        "version": 1,
        "content": content
    }


def search_jira_issues_by_label(access_token: str, cloud_id: str, label: str) -> List[dict]:
    """Busca issues do Jira por label usando a nova API search/jql."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search/jql'
    
    all_issues = []
    next_page_token = None
    
    while True:
        params = {
            "jql": f'labels = "{label}" ORDER BY key ASC',
            "maxResults": 100,
            "fields": "key,summary,description,labels"
        }
        
        if next_page_token:
            params["nextPageToken"] = next_page_token
        
        response = requests.get(
            url,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            },
            params=params
        )
        
        if response.status_code != 200:
            print(f"Erro ao buscar issues: {response.status_code}")
            print(response.text)
            break
        
        data = response.json()
        issues = data.get('issues', [])
        all_issues.extend(issues)
        
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break
        
        time.sleep(0.5)
    
    return all_issues


def match_issues_with_cards(issues: List[dict], cards: Dict[str, dict]) -> Dict[str, str]:
    """Mapeia issues do Jira com cards do documento."""
    mapping = {}
    
    title_to_card = {}
    for card_id, card_data in cards.items():
        parsed = parse_yaml_content(card_data['yaml_content'])
        titulo = parsed.get('Titulo', card_data['title'])
        
        clean_title = re.sub(r'^\[[^\]]+\]\s*', '', titulo).strip().lower()
        title_to_card[clean_title] = card_id
        
        original_title = card_data['title'].strip().lower()
        title_to_card[original_title] = card_id
    
    for issue in issues:
        key = issue['key']
        summary = issue['fields']['summary']
        
        clean_summary = re.sub(r'^\[[^\]]+\]\s*', '', summary).strip().lower()
        
        if clean_summary in title_to_card:
            mapping[title_to_card[clean_summary]] = key
        else:
            for title, card_id in title_to_card.items():
                if title in clean_summary or clean_summary in title:
                    if card_id not in mapping:
                        mapping[card_id] = key
                    break
    
    return mapping


def update_jira_issue(access_token: str, cloud_id: str, issue_key: str, description_adf: dict) -> dict:
    """Atualiza uma issue no Jira."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}'
    
    try:
        response = requests.put(
            url,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json={'fields': {'description': description_adf}}
        )
        
        if response.status_code == 204:
            return {'success': True, 'key': issue_key}
        else:
            return {
                'success': False, 
                'key': issue_key,
                'error': response.json() if response.text else {'status': response.status_code}
            }
    except Exception as e:
        return {'success': False, 'key': issue_key, 'error': str(e)}


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


def parse_yaml_field(yaml_content: str, field_name: str) -> Optional[str]:
    """Extrai um campo específico do YAML."""
    pattern = rf'^{field_name}:\s*(.+?)$'
    match = re.search(pattern, yaml_content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def main():
    print("=" * 60)
    print("ATUALIZAÇÃO DE CARDS MENU CONFIGURAÇÕES NO JIRA")
    print("=" * 60)
    
    print("\n1. Obtendo credenciais do Jira...")
    try:
        access_token, cloud_id = get_jira_credentials()
        print(f"   ✅ Cloud ID: {cloud_id}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return
    
    print("\n2. Lendo cards do documento...")
    doc_path = 'docs/configuracoes-admin-cards-jira.md'
    cards = extract_all_cards_from_document(doc_path)
    print(f"   ✅ {len(cards)} cards encontrados no documento")
    
    print("\n3. Buscando issues no Jira com label 'menu-config'...")
    issues = search_jira_issues_by_label(access_token, cloud_id, 'menu-config')
    print(f"   ✅ {len(issues)} issues encontradas no Jira")
    
    print("\n4. Mapeando cards com issues do Jira...")
    mapping = match_issues_with_cards(issues, cards)
    print(f"   ✅ {len(mapping)} cards mapeados com issues")
    
    print("\n   Exemplos de mapeamento:")
    for card_id, issue_key in list(mapping.items())[:5]:
        print(f"      {card_id} -> {issue_key}")
    
    print("\n5. Atualizando descrições das issues...")
    success_count = 0
    error_count = 0
    errors = []
    
    for card_id, issue_key in mapping.items():
        card_data = cards.get(card_id)
        if not card_data:
            continue
        
        adf_description = yaml_to_jira_adf(card_id, card_data['yaml_content'])
        
        result = update_jira_issue(access_token, cloud_id, issue_key, adf_description)
        
        if result['success']:
            success_count += 1
            print(f"   ✅ {issue_key} ({card_id}) - Atualizado")
        else:
            error_count += 1
            errors.append(result)
            print(f"   ❌ {issue_key} ({card_id}) - Erro: {result.get('error', 'Unknown')}")
        
        time.sleep(0.3)
    
    print("\n6. Adicionando labels de Sprint e Epic...")
    label_success = 0
    
    for card_id, issue_key in mapping.items():
        card = cards.get(card_id)
        if not card:
            continue
        
        yaml_content = card['yaml_content']
        
        sprint = parse_yaml_field(yaml_content, 'Sprint')
        epic = parse_yaml_field(yaml_content, 'Epic')
        
        labels_to_add = []
        
        if sprint:
            sprint_label = f"sprint-{sprint}"
            labels_to_add.append(sprint_label)
        
        if epic:
            epic_match = re.search(r'EPIC-(\d+)', epic)
            if epic_match:
                epic_num = epic_match.group(1)
                epic_label = f"epic-config-{epic_num}"
                labels_to_add.append(epic_label)
        
        if labels_to_add:
            result = add_labels_to_issue(access_token, cloud_id, issue_key, labels_to_add)
            if result:
                label_success += 1
                print(f"   ✅ {issue_key} ({card_id}) - Labels: {', '.join(labels_to_add)}")
        
        time.sleep(0.2)
    
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Cards no documento: {len(cards)}")
    print(f"Issues no Jira: {len(issues)}")
    print(f"Cards mapeados: {len(mapping)}")
    print(f"Descrições atualizadas: {success_count}")
    print(f"Labels adicionadas: {label_success}")
    print(f"Erros: {error_count}")
    
    not_mapped = set(cards.keys()) - set(mapping.keys())
    if not_mapped:
        print(f"\nCards não mapeados ({len(not_mapped)}):")
        for card_id in sorted(not_mapped):
            print(f"   - {card_id}: {cards[card_id]['title']}")
    
    result = {
        'total_cards': len(cards),
        'total_issues': len(issues),
        'mapped': len(mapping),
        'success': success_count,
        'labels_added': label_success,
        'errors': error_count,
        'mapping': mapping,
        'not_mapped': list(not_mapped),
        'error_details': errors
    }
    
    with open('scripts/jira-config-update-result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResultado salvo em scripts/jira-config-update-result.json")


if __name__ == '__main__':
    main()
