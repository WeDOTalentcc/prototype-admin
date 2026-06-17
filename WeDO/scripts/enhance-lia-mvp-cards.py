#!/usr/bin/env python3
"""
Script para melhorar os cards do lia-mvp-cards-jira.md
Adiciona seções faltantes baseado no template de configuracoes-admin-cards-jira.md
"""

import re
import os

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def is_frontend_card(yaml_content):
    """Verifica se o card é de Frontend"""
    titulo = re.search(r'^Titulo:\s*\[([^\]]+)\]', yaml_content, re.MULTILINE)
    if titulo:
        tipo = titulo.group(1).upper()
        return 'FRONTEND' in tipo or 'FULL-STACK' in tipo or 'FULL STACK' in tipo
    return False

def has_section(yaml_content, section_name):
    """Verifica se uma seção existe no YAML"""
    pattern = rf'^{section_name}:\s*$'
    return bool(re.search(pattern, yaml_content, re.MULTILINE))

def get_card_title(yaml_content):
    """Extrai o título do card"""
    match = re.search(r'^Titulo:\s*(.+)$', yaml_content, re.MULTILINE)
    return match.group(1).strip() if match else "Unknown"

def generate_referencias_design():
    """Gera seção de Referências de Design padrão"""
    return """
Referencias de Design:
  Figma: "[A ser preenchido pelo time de Design]"
  Storybook:
    URL: "[A ser preenchido]"
    Componentes relacionados:
      - "[Listar componentes]"
  Assets:
    - "[Listar ícones/imagens necessários]"
  Tokens:
    - "accent-primary: #60BED1"
    - "bg-primary: #FFFFFF"
    - "text-primary: #111827"
"""

def generate_acessibilidade():
    """Gera seção de Acessibilidade padrão"""
    return """  Acessibilidade:
    - Keyboard navigation (Tab, Enter, Space, Escape)
    - Labels e placeholders descritivos
    - ARIA-labels em elementos interativos
    - Focus visible em todos os elementos clicáveis
    - Mensagens de erro anunciadas por screen readers
    - Contraste mínimo WCAG AA (4.5:1)
"""

def add_missing_sections(yaml_content, card_id):
    """Adiciona seções faltantes a um card"""
    modified = yaml_content
    changes = []
    
    is_frontend = is_frontend_card(yaml_content)
    
    if is_frontend:
        # Adicionar Referencias de Design se não existir
        if not has_section(yaml_content, 'Referencias de Design'):
            # Inserir antes de DoD ou no final
            if 'DoD:' in modified:
                modified = modified.replace('DoD:', generate_referencias_design() + '\nDoD:')
                changes.append('Referencias de Design')
            elif 'Criterios de Aceita' in modified:
                modified = modified.replace('Criterios de Aceita', generate_referencias_design() + '\nCriterios de Aceita')
                changes.append('Referencias de Design')
        
        # Verificar e adicionar Acessibilidade dentro de Design & Componentes
        if 'Design & Componentes:' in modified and 'Acessibilidade:' not in modified:
            # Encontrar onde inserir Acessibilidade (antes de Comportamento ou DoD)
            if 'Comportamento de UI:' in modified:
                modified = modified.replace('Comportamento de UI:', generate_acessibilidade() + '\nComportamento de UI:')
                changes.append('Acessibilidade')
            elif 'Comportamento de API:' in modified:
                modified = modified.replace('Comportamento de API:', generate_acessibilidade() + '\nComportamento de API:')
                changes.append('Acessibilidade')
    
    return modified, changes

def process_cards(content):
    """Processa todos os cards do documento"""
    # Regex para encontrar blocos de cards YAML
    card_pattern = r'(### CARD [^\n]+\n\n```yaml\n)([\s\S]*?)(```)'
    
    stats = {
        'total': 0,
        'frontend': 0,
        'modified': 0,
        'referencias_added': 0,
        'acessibilidade_added': 0
    }
    
    def replace_card(match):
        header = match.group(1)
        yaml_content = match.group(2)
        footer = match.group(3)
        
        stats['total'] += 1
        
        # Extrair ID do card do header
        card_id_match = re.search(r'CARD ([A-Z]+-\d+)', header)
        card_id = card_id_match.group(1) if card_id_match else f"CARD-{stats['total']}"
        
        if is_frontend_card(yaml_content):
            stats['frontend'] += 1
            
        modified_yaml, changes = add_missing_sections(yaml_content, card_id)
        
        if changes:
            stats['modified'] += 1
            if 'Referencias de Design' in changes:
                stats['referencias_added'] += 1
            if 'Acessibilidade' in changes:
                stats['acessibilidade_added'] += 1
            print(f"  {card_id}: +{', '.join(changes)}")
        
        return header + modified_yaml + footer
    
    modified_content = re.sub(card_pattern, replace_card, content)
    
    return modified_content, stats

def main():
    input_path = 'docs/lia-mvp-cards-jira.md'
    
    print("=" * 60)
    print("Melhorando cards do lia-mvp-cards-jira.md")
    print("=" * 60)
    print()
    
    if not os.path.exists(input_path):
        print(f"Arquivo não encontrado: {input_path}")
        return
    
    content = read_file(input_path)
    print(f"Arquivo lido: {len(content)} caracteres")
    print()
    
    print("Processando cards...")
    modified_content, stats = process_cards(content)
    
    print()
    print("=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Total de cards: {stats['total']}")
    print(f"Cards Frontend/Full-Stack: {stats['frontend']}")
    print(f"Cards modificados: {stats['modified']}")
    print(f"  - Referencias de Design adicionadas: {stats['referencias_added']}")
    print(f"  - Acessibilidade adicionada: {stats['acessibilidade_added']}")
    print()
    
    if stats['modified'] > 0:
        write_file(input_path, modified_content)
        print(f"Arquivo atualizado: {input_path}")
    else:
        print("Nenhuma modificação necessária.")

if __name__ == '__main__':
    main()
