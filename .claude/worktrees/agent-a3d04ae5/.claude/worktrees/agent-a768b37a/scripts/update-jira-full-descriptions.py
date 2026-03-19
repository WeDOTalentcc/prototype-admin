#!/usr/bin/env python3
"""
Script para atualizar os cards do Jira com descrições completas do documento lia-mvp-cards-jira.md.

Atualiza:
- Campo Description com todas as informações do card
- Campo Sprint com o número correto
- Campo Epic com o épico correspondente
- Labels adicionais se necessário
"""

import os
import re
import json
import time
import requests
from typing import Dict, List, Tuple, Optional

# Mapeamento de Card IDs do documento para Jira Issue Keys
# Baseado na importação original: WT-893 a WT-1036 (144 cards MVP)
# Este mapeamento será construído dinamicamente buscando no Jira

# Mapeamento de Epic IDs
EPIC_MAPPING = {
    "EPIC-AUTH": "Autenticação",
    "EPIC-WIZARD": "Wizard Conversacional",
    "EPIC-MAPPING": "Busca e Mapeamento",
    "EPIC-WSI": "Geração de Perguntas WSI",
    "EPIC-TRIAGEM": "Triagem WhatsApp",
    "EPIC-SCORE": "Score WSI",
    "EPIC-GATES": "Gates de Aprovação",
    "EPIC-TEMPLATES": "Templates de Comunicação",
    "EPIC-AGENDAMENTO": "Agendamento",
    "EPIC-NOTIFICACOES": "Notificações",
    "EPIC-KANBAN": "Kanban e Tabela",
    "EPIC-JD": "JD e Wizard Avançado",
    "EPIC-CONFIG": "Configurações Avançadas",
    "EPIC-INTEGRACOES": "Integrações MVP",
    "EPIC-AGENTES": "Agentes IA"
}


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
    
    # Get cloud ID
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
    
    # Pattern para encontrar cards: ### CARD ID-XXX: Título seguido de bloco yaml
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
        # Verifica se é uma chave de primeiro nível
        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            # Salva a chave anterior
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
    
    # Salva última chave
    if current_key:
        result[current_key] = '\n'.join(current_value).strip()
    
    return result


def yaml_to_jira_adf(card_id: str, yaml_content: str) -> dict:
    """Converte conteúdo YAML completo para formato ADF do Jira."""
    parsed = parse_yaml_content(yaml_content)
    
    content = []
    
    # Cabeçalho com Card ID
    content.append({
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": f"Card {card_id}", "marks": [{"type": "strong"}]}]
    })
    
    # Campos principais em ordem
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
        ("Criterios de Aceitacao", "Critérios de Aceitação"),
        ("Dependencias", "Dependências")
    ]
    
    for yaml_key, display_name in field_order:
        if yaml_key in parsed and parsed[yaml_key]:
            value = parsed[yaml_key]
            
            # Adiciona heading da seção
            content.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": display_name}]
            })
            
            # Processa o conteúdo
            lines = value.split('\n')
            
            # Se tem itens com bullet points
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
                # Texto simples em parágrafos
                text_content = ' '.join(line.strip() for line in lines if line.strip())
                if text_content:
                    content.append({
                        "type": "paragraph",
                        "content": [{"type": "text", "text": text_content}]
                    })
    
    # Informações técnicas
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


def search_jira_issues_by_label(access_token: str, cloud_id: str, label: str = "lia-mvp", max_results: int = 200) -> List[dict]:
    """Busca issues do Jira por label usando a nova API search/jql."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search/jql'
    
    all_issues = []
    next_page_token = None
    
    while True:
        params = {
            "jql": f'labels = "{label}" ORDER BY key ASC',
            "maxResults": 100,
            "fields": "key,summary,description,labels,customfield_10020,parent"
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
        
        # Verifica se há mais páginas
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break
        
        time.sleep(0.5)  # Rate limiting
    
    return all_issues


def extract_card_id_from_summary(summary: str) -> Optional[str]:
    """Extrai o Card ID do título da issue."""
    # Padrões: [FRONTEND] Tela de Login ou AUTH-001: Tela de Login
    # Busca pelo padrão de prefixo do título
    
    # Primeiro, tenta extrair do início do summary se tiver o card ID
    patterns = [
        r'^([A-Z]+-\d+)\s*[:\-]',  # AUTH-001: ou AUTH-001 -
        r'\[([A-Z]+-\d+)\]',       # [AUTH-001]
    ]
    
    for pattern in patterns:
        match = re.search(pattern, summary)
        if match:
            return match.group(1)
    
    # Se não encontrou, tenta mapear pelo título
    return None


def match_issues_with_cards(issues: List[dict], cards: Dict[str, dict]) -> Dict[str, str]:
    """Mapeia issues do Jira com cards do documento."""
    mapping = {}
    
    # Primeiro, cria mapeamento por título normalizado
    title_to_card = {}
    for card_id, card_data in cards.items():
        # Extrai título do YAML
        parsed = parse_yaml_content(card_data['yaml_content'])
        titulo = parsed.get('Titulo', card_data['title'])
        
        # Remove prefixos [FRONTEND], [BACKEND], etc
        clean_title = re.sub(r'^\[[^\]]+\]\s*', '', titulo).strip().lower()
        title_to_card[clean_title] = card_id
        
        # Também mapeia pelo título original do heading
        original_title = card_data['title'].strip().lower()
        title_to_card[original_title] = card_id
    
    # Agora mapeia as issues
    for issue in issues:
        key = issue['key']
        summary = issue['fields']['summary']
        
        # Limpa o summary
        clean_summary = re.sub(r'^\[[^\]]+\]\s*', '', summary).strip().lower()
        
        # Busca correspondência
        if clean_summary in title_to_card:
            mapping[title_to_card[clean_summary]] = key
        else:
            # Tenta match parcial
            for title, card_id in title_to_card.items():
                if title in clean_summary or clean_summary in title:
                    mapping[card_id] = key
                    break
    
    return mapping


def update_jira_issue(access_token: str, cloud_id: str, issue_key: str, 
                      description_adf: dict, sprint_id: Optional[str] = None,
                      epic_key: Optional[str] = None) -> dict:
    """Atualiza uma issue no Jira."""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key}'
    
    fields = {
        'description': description_adf
    }
    
    # Sprint field (customfield_10020 é comum, mas pode variar)
    if sprint_id:
        fields['customfield_10020'] = sprint_id
    
    # Epic (parent para issues em épicos)
    if epic_key:
        fields['parent'] = {'key': epic_key}
    
    try:
        response = requests.put(
            url,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json={'fields': fields}
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


def main():
    print("=" * 60)
    print("ATUALIZAÇÃO DE DESCRIÇÕES COMPLETAS NO JIRA")
    print("=" * 60)
    
    # 1. Obter credenciais
    print("\n1. Obtendo credenciais do Jira...")
    try:
        access_token, cloud_id = get_jira_credentials()
        print(f"   ✅ Cloud ID: {cloud_id}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return
    
    # 2. Ler cards do documento
    print("\n2. Lendo cards do documento...")
    doc_path = 'docs/lia-mvp-cards-jira.md'
    cards = extract_all_cards_from_document(doc_path)
    print(f"   ✅ {len(cards)} cards encontrados no documento")
    
    # 3. Buscar issues no Jira
    print("\n3. Buscando issues no Jira com label 'lia-mvp'...")
    issues = search_jira_issues_by_label(access_token, cloud_id, 'lia-mvp')
    print(f"   ✅ {len(issues)} issues encontradas no Jira")
    
    # 4. Mapear cards com issues
    print("\n4. Mapeando cards com issues do Jira...")
    mapping = match_issues_with_cards(issues, cards)
    print(f"   ✅ {len(mapping)} cards mapeados com issues")
    
    # Mostrar alguns exemplos
    print("\n   Exemplos de mapeamento:")
    for card_id, issue_key in list(mapping.items())[:5]:
        print(f"      {card_id} -> {issue_key}")
    
    # 5. Atualizar issues
    print("\n5. Atualizando descrições das issues...")
    success_count = 0
    error_count = 0
    errors = []
    
    for card_id, issue_key in mapping.items():
        card_data = cards.get(card_id)
        if not card_data:
            continue
        
        # Gerar ADF da descrição
        adf_description = yaml_to_jira_adf(card_id, card_data['yaml_content'])
        
        # Extrair sprint do YAML
        parsed = parse_yaml_content(card_data['yaml_content'])
        sprint_num = parsed.get('Sprint', '').strip()
        
        # Atualizar issue
        result = update_jira_issue(
            access_token, 
            cloud_id, 
            issue_key, 
            adf_description
        )
        
        if result['success']:
            success_count += 1
            print(f"   ✅ {issue_key} ({card_id}) - Atualizado")
        else:
            error_count += 1
            errors.append(result)
            print(f"   ❌ {issue_key} ({card_id}) - Erro: {result.get('error', 'Unknown')}")
        
        # Rate limiting
        time.sleep(0.3)
    
    # 6. Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Cards no documento: {len(cards)}")
    print(f"Issues no Jira: {len(issues)}")
    print(f"Cards mapeados: {len(mapping)}")
    print(f"Atualizações bem-sucedidas: {success_count}")
    print(f"Erros: {error_count}")
    
    # Salvar resultado
    result = {
        'total_cards': len(cards),
        'total_issues': len(issues),
        'mapped': len(mapping),
        'success': success_count,
        'errors': error_count,
        'mapping': mapping,
        'error_details': errors
    }
    
    with open('scripts/jira-full-update-result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResultado salvo em scripts/jira-full-update-result.json")


if __name__ == '__main__':
    main()
