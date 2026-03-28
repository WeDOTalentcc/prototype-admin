"""
Conversor de cards YAML para formato da API Jira.

Este módulo mapeia os campos do formato YAML usado nos arquivos .md
para o formato esperado pela API REST do Jira v3 (Atlassian Document Format).
"""

from typing import Dict, Any, List, Optional
import re


PRIORITY_MAP = {
    'alta': 'High',
    'high': 'High',
    'media': 'Medium',
    'medium': 'Medium',
    'média': 'Medium',
    'baixa': 'Low',
    'low': 'Low',
    'urgente': 'Highest',
    'highest': 'Highest',
    'critica': 'Highest',
    'critical': 'Highest',
}

ISSUE_TYPE_MAP = {
    # Projeto WT (wedotalent teste) só tem: Task, Epic, Subtask
    'feature': 'Task',
    'story': 'Task',
    'task': 'Task',
    'tarefa': 'Task',
    'bug': 'Task',
    'epic': 'Epic',
    'subtask': 'Subtask',
    'sub-task': 'Subtask',
    'improvement': 'Task',
    'melhoria': 'Task',
}


def text_to_adf(text: str) -> Dict[str, Any]:
    """
    Converte texto/markdown simples para Atlassian Document Format (ADF).
    
    Args:
        text: Texto em formato Markdown simples
        
    Returns:
        Documento no formato ADF para API Jira v3
    """
    content = []
    
    if not text:
        return {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Sem descrição"}]}]
        }
    
    lines = text.strip().split('\n')
    current_paragraph = []
    in_list = False
    list_items = []
    
    for line in lines:
        line = line.rstrip()
        
        if line.startswith('## '):
            if current_paragraph:
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": ' '.join(current_paragraph)}]
                })
                current_paragraph = []
            if in_list and list_items:
                content.append({
                    "type": "bulletList",
                    "content": list_items
                })
                list_items = []
                in_list = False
            
            content.append({
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": line[3:].strip()}]
            })
        
        elif line.startswith('### '):
            if current_paragraph:
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": ' '.join(current_paragraph)}]
                })
                current_paragraph = []
            if in_list and list_items:
                content.append({
                    "type": "bulletList",
                    "content": list_items
                })
                list_items = []
                in_list = False
            
            content.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": line[4:].strip()}]
            })
        
        elif line.startswith('- ') or line.startswith('* '):
            if current_paragraph:
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": ' '.join(current_paragraph)}]
                })
                current_paragraph = []
            
            in_list = True
            item_text = line[2:].strip()
            item_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', item_text)
            
            list_items.append({
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": item_text}]
                }]
            })
        
        elif line.startswith('---'):
            if current_paragraph:
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": ' '.join(current_paragraph)}]
                })
                current_paragraph = []
            if in_list and list_items:
                content.append({
                    "type": "bulletList",
                    "content": list_items
                })
                list_items = []
                in_list = False
            
            content.append({"type": "rule"})
        
        elif line.strip() == '':
            if in_list and list_items:
                content.append({
                    "type": "bulletList",
                    "content": list_items
                })
                list_items = []
                in_list = False
            if current_paragraph:
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": ' '.join(current_paragraph)}]
                })
                current_paragraph = []
        
        else:
            if in_list and list_items:
                content.append({
                    "type": "bulletList",
                    "content": list_items
                })
                list_items = []
                in_list = False
            
            clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line.strip())
            current_paragraph.append(clean_line)
    
    if current_paragraph:
        content.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": ' '.join(current_paragraph)}]
        })
    if in_list and list_items:
        content.append({
            "type": "bulletList",
            "content": list_items
        })
    
    if not content:
        content = [{"type": "paragraph", "content": [{"type": "text", "text": "Sem descrição"}]}]
    
    return {
        "type": "doc",
        "version": 1,
        "content": content
    }


def format_description(data: Dict[str, Any]) -> str:
    """
    Formata a descrição do card com todas as seções em Markdown.
    PRIORIZA o conteúdo completo (_full_content) para garantir 100% das informações.
    
    Args:
        data: Dados do card extraídos do YAML
        
    Returns:
        String formatada em Markdown para a descrição do Jira
    """
    sections = []
    
    # PRIORIDADE: Se temos o conteúdo completo extraído, usar ele diretamente
    if data.get('_full_content'):
        full_content = data['_full_content']
        # Limpar e formatar o conteúdo
        sections.append(full_content)
        return '\n\n'.join(sections)
    
    # Fallback: usar campos individuais (compatibilidade com formato antigo)
    if data.get('Descricao'):
        sections.append(f"## Descrição\n\n{_format_text(data['Descricao'])}")
    
    if data.get('Historia de Usuario'):
        sections.append(f"## História de Usuário\n\n{_format_text(data['Historia de Usuario'])}")
    
    if data.get('Regras de Negocio'):
        regras = data['Regras de Negocio']
        if isinstance(regras, list):
            formatted = '\n'.join(f"- {item}" for item in regras)
        elif isinstance(regras, dict):
            formatted = '\n'.join(f"- **{k}**: {v}" for k, v in regras.items())
        else:
            formatted = _format_text(regras)
        sections.append(f"## Regras de Negócio\n\n{formatted}")
    
    if data.get('Requisitos Tecnicos'):
        req = data['Requisitos Tecnicos']
        formatted = _format_nested_dict(req)
        sections.append(f"## Requisitos Técnicos\n\n{formatted}")
    
    if data.get('Integracoes Externas'):
        integracoes = data['Integracoes Externas']
        formatted = _format_nested_dict(integracoes)
        sections.append(f"## Integrações Externas\n\n{formatted}")
    
    if data.get('Design & Componentes'):
        design = data['Design & Componentes']
        formatted = _format_nested_dict(design)
        sections.append(f"## Design & Componentes\n\n{formatted}")
    
    if data.get('Comportamento de UI'):
        ui = data['Comportamento de UI']
        formatted = _format_nested_dict(ui)
        sections.append(f"## Comportamento de UI\n\n{formatted}")
    
    if data.get('DoD') or data.get('DoD (Definition of Done)'):
        dod = data.get('DoD') or data.get('DoD (Definition of Done)')
        formatted = _format_checklist(dod)
        sections.append(f"## Definition of Done (DoD)\n\n{formatted}")
    
    if data.get('Criterios de Aceitacao'):
        criterios = data['Criterios de Aceitacao']
        formatted = _format_checklist(criterios)
        sections.append(f"## Critérios de Aceitação\n\n{formatted}")
    
    if data.get('Dependencias'):
        deps = data['Dependencias']
        if isinstance(deps, list):
            formatted = ', '.join(deps)
        else:
            formatted = str(deps)
        sections.append(f"## Dependências\n\n{formatted}")
    
    if data.get('Labels'):
        labels = data['Labels']
        if isinstance(labels, str):
            labels = [l.strip() for l in labels.split(',')]
        sections.append(f"## Labels\n\n{', '.join(labels)}")
    
    return '\n\n---\n\n'.join(sections)


def _format_text(text: Any) -> str:
    """Formata texto removendo indentação excessiva."""
    if not text:
        return ''
    if not isinstance(text, str):
        return str(text)
    
    lines = text.strip().split('\n')
    return '\n'.join(line.strip() for line in lines)


def _format_nested_dict(data: Any, level: int = 0) -> str:
    """Formata dicionários aninhados como Markdown."""
    if data is None:
        return ''
    
    if isinstance(data, str):
        return data
    
    if isinstance(data, list):
        return '\n'.join(f"{'  ' * level}- {_format_nested_dict(item, level + 1)}" for item in data)
    
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{'  ' * level}**{key}:**")
                lines.append(_format_nested_dict(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"{'  ' * level}**{key}:**")
                for item in value:
                    lines.append(f"{'  ' * (level + 1)}- {_format_nested_dict(item, level + 2)}")
            else:
                lines.append(f"{'  ' * level}- **{key}:** {value}")
        return '\n'.join(lines)
    
    return str(data)


def _format_checklist(items: Any) -> str:
    """Formata itens como checklist Markdown."""
    if not items:
        return ''
    
    if isinstance(items, str):
        lines = items.strip().split('\n')
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('- [ ]'):
                formatted_lines.append(line)
            elif line.startswith('-'):
                formatted_lines.append(f"- [ ] {line[1:].strip()}")
            elif line:
                formatted_lines.append(f"- [ ] {line}")
        return '\n'.join(formatted_lines)
    
    if isinstance(items, list):
        return '\n'.join(f"- [ ] {_clean_checklist_item(item)}" for item in items)
    
    if isinstance(items, dict):
        lines = []
        for key, value in items.items():
            lines.append(f"- [ ] {key}: {value}")
        return '\n'.join(lines)
    
    return str(items)


def _clean_checklist_item(item: str) -> str:
    """Remove marcadores existentes de um item de checklist."""
    if not isinstance(item, str):
        return str(item)
    
    item = item.strip()
    item = item.lstrip('- ')
    item = item.replace('[ ]', '').replace('[x]', '').replace('[X]', '')
    return item.strip()


def generate_labels(card_id: str, hub: Optional[str], data: Dict[str, Any]) -> List[str]:
    """
    Gera labels para o card Jira.
    
    Args:
        card_id: ID do card (ex: EMP-001)
        hub: Nome do hub/seção
        data: Dados do card
        
    Returns:
        Lista de labels
    """
    labels = []
    
    labels.append(f"card-id:{card_id}")
    
    if hub:
        labels.append(f"hub:{hub}")
    
    if data.get('Labels'):
        existing = data['Labels']
        if isinstance(existing, str):
            existing = [l.strip() for l in existing.split(',')]
        labels.extend(existing)
    
    tipo = data.get('Tipo', '').lower()
    if tipo and tipo not in ['feature', 'task', 'bug', 'epic']:
        # Remover espaços das labels (Jira não permite espaços)
        tipo_sanitizado = tipo.replace(' ', '-')
        labels.append(f"tipo:{tipo_sanitizado}")
    
    labels.append("sync:jira-md")
    
    # Sanitizar todas as labels para remover espaços
    sanitized_labels = [label.replace(' ', '-') for label in labels]
    
    return list(set(sanitized_labels))


def convert_card_to_jira(
    card: Dict[str, Any],
    project_key: str = 'WT',
    story_points_field: Optional[str] = None,
    sprint_field: Optional[str] = None,
    epic_link_field: Optional[str] = None
) -> Dict[str, Any]:
    """
    Converte um card do formato YAML para payload da API Jira.
    
    Args:
        card: Dicionário com dados do card (id, hub, data, source_file)
        project_key: Chave do projeto Jira
        story_points_field: ID do campo de Story Points
        sprint_field: ID do campo de Sprint (opcional)
        epic_link_field: ID do campo de Epic Link
        
    Returns:
        Payload formatado para a API do Jira
    """
    data = card['data']
    card_id = card['id']
    hub = card.get('hub')
    
    titulo = data.get('Titulo', data.get('titulo', ''))
    titulo = titulo.replace('[FULL-STACK]', '').replace('[FRONTEND]', '').replace('[BACKEND]', '')
    titulo = titulo.replace('[FRONT]', '').replace('[BACK]', '').strip()
    
    tipo_raw = data.get('Tipo', 'Task').lower()
    issue_type = ISSUE_TYPE_MAP.get(tipo_raw, 'Task')
    
    prioridade_raw = data.get('Prioridade', 'Medium').lower()
    priority = PRIORITY_MAP.get(prioridade_raw, 'Medium')
    
    description_md = format_description(data)
    description_adf = text_to_adf(description_md)
    
    labels = generate_labels(card_id, hub, data)
    
    payload = {
        'fields': {
            'project': {'key': project_key},
            'summary': f"[{card_id}] {titulo}",
            'description': description_adf,
            'issuetype': {'name': issue_type},
            'priority': {'name': priority},
            'labels': labels,
        }
    }
    
    pontos = data.get('Pontos')
    if pontos is not None and story_points_field:
        try:
            payload['fields'][story_points_field] = float(pontos)
        except (ValueError, TypeError):
            pass
    
    epic = data.get('Epic')
    if epic and epic_link_field:
        payload['fields'][epic_link_field] = epic
    
    return payload


def get_summary_for_search(card: Dict[str, Any]) -> str:
    """
    Gera o summary para busca no Jira.
    
    Args:
        card: Dados do card
        
    Returns:
        String do summary para busca
    """
    data = card['data']
    titulo = data.get('Titulo', data.get('titulo', ''))
    return f"[{card['id']}] {titulo}"


if __name__ == '__main__':
    from parser import parse_markdown_file, list_markdown_files
    
    print("Testando conversão de cards...")
    print("=" * 60)
    
    md_files = list_markdown_files()
    
    if md_files:
        test_file = md_files[0]
        print(f"\nArquivo: {test_file}")
        
        cards = parse_markdown_file(str(test_file))
        
        if cards:
            card = cards[0]
            print(f"\nCard: {card['id']}")
            print(f"Hub: {card['hub']}")
            
            payload = convert_card_to_jira(card)
            
            print(f"\nPayload Jira:")
            print(f"  Summary: {payload['fields']['summary']}")
            print(f"  Type: {payload['fields']['issuetype']['name']}")
            print(f"  Priority: {payload['fields']['priority']['name']}")
            print(f"  Labels: {payload['fields']['labels']}")
            print(f"\n  Description (primeiros 500 chars):")
            print(f"  {payload['fields']['description'][:500]}...")
