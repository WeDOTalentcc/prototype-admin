"""
Parser de arquivos .md para extração de cards Jira.

Este módulo extrai blocos YAML de arquivos Markdown e os converte
em dicionários Python estruturados.
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional


def extract_yaml_blocks(content: str) -> List[str]:
    """
    Extrai todos os blocos YAML de um conteúdo Markdown.
    
    Args:
        content: Conteúdo do arquivo Markdown
        
    Returns:
        Lista de strings com o conteúdo YAML de cada bloco
    """
    pattern = r'```yaml\s*\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    return matches


def preprocess_yaml(yaml_content: str) -> str:
    """
    Pré-processa o YAML para lidar com caracteres especiais.
    
    Trata casos como:
    - Titulo: [FRONTEND] Text (interpreta como lista incorretamente)
    - - [ ] Item (checkbox markdown)
    - Listas numeradas com ":" no meio (ex: "2. Categoria: Saude")
    - Caracteres especiais como "@"
    
    Args:
        yaml_content: String YAML original
        
    Returns:
        String YAML com valores problemáticos escapados
    """
    lines = yaml_content.split('\n')
    processed_lines = []
    
    in_multiline_block = False
    
    for i, line in enumerate(lines):
        original_line = line
        
        # Escape Titulo com colchetes
        if re.match(r'^(\s*)Titulo:\s*\[', line):
            match = re.match(r'^(\s*Titulo:\s*)(.+)$', line)
            if match:
                prefix = match.group(1)
                value = match.group(2)
                if not (value.startswith('"') or value.startswith("'")):
                    line = f'{prefix}"{value}"'
        
        # Escape checkboxes markdown
        if re.match(r'^\s*-\s*\[\s*[xX ]?\s*\]', line):
            match = re.match(r'^(\s*-\s*)(\[\s*[xX ]?\s*\]\s*.*)$', line)
            if match:
                prefix = match.group(1)
                value = match.group(2)
                line = f'{prefix}"{value}"'
        
        # Escape itens de lista numerada com ":" no valor (ex: "1. Nome: valor")
        # Detecta: espaços + número + ponto + texto com ":"
        if re.match(r'^\s+\d+\.\s+.+:.+', line):
            match = re.match(r'^(\s+)(\d+\.\s+.+)$', line)
            if match:
                indent = match.group(1)
                value = match.group(2)
                if not (value.startswith('"') or value.startswith("'")):
                    # Escape aspas dentro do valor
                    value = value.replace('"', '\\"')
                    line = f'{indent}"{value}"'
        
        # Escape linhas com "@" que não são chaves
        if '@' in line and not re.match(r'^\s*\w+:', line):
            match = re.match(r'^(\s*-\s*)(.+)$', line)
            if match:
                prefix = match.group(1)
                value = match.group(2)
                if not (value.startswith('"') or value.startswith("'")):
                    value = value.replace('"', '\\"')
                    line = f'{prefix}"{value}"'
        
        # Escape valores de lista simples com ":" no meio
        if re.match(r'^\s+-\s+[^"\']+:.+', line):
            match = re.match(r'^(\s+-\s+)([^"\']+:.+)$', line)
            if match:
                prefix = match.group(1)
                value = match.group(2)
                # Só escapa se não parecer ser uma chave YAML válida
                if not re.match(r'^[a-zA-Z_]\w*:\s', value):
                    value = value.replace('"', '\\"')
                    line = f'{prefix}"{value}"'
        
        processed_lines.append(line)
    
    return '\n'.join(processed_lines)


def extract_fields_via_regex(yaml_content: str) -> Dict[str, Any]:
    """
    Extrai campos do YAML via regex quando o parsing YAML falha.
    
    Args:
        yaml_content: String com conteúdo YAML
        
    Returns:
        Dicionário com campos extraídos
    """
    result = {}
    
    # Extrair campos simples de linha única
    simple_fields = [
        ('Titulo', r'^Titulo:\s*["\']?(.+?)["\']?\s*$'),
        ('Tipo', r'^Tipo:\s*(\w+)'),
        ('Sprint', r'^Sprint:\s*(\d+)'),
        ('Pontos', r'^Pontos:\s*(\d+)'),
        ('Prioridade', r'^Prioridade:\s*(\w+)'),
        ('Epic', r'^Epic:\s*([\w-]+)'),
        ('Status', r'^Status:\s*(\w+)'),
    ]
    
    lines = yaml_content.split('\n')
    
    for field_name, pattern in simple_fields:
        for line in lines:
            match = re.match(pattern, line.strip(), re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Converter tipos
                if field_name in ['Sprint', 'Pontos']:
                    try:
                        value = int(value)
                    except:
                        pass
                result[field_name] = value
                break
    
    # Extrair campos multiline
    multiline_fields = ['Descricao', 'Historia de Usuario']
    
    for field_name in multiline_fields:
        pattern = rf'^{field_name}:\s*\|?\s*\n((?:\s+.+\n?)+)'
        match = re.search(pattern, yaml_content, re.MULTILINE)
        if match:
            result[field_name] = match.group(1).strip()
    
    return result


def parse_yaml_block(yaml_content: str) -> Optional[Dict[str, Any]]:
    """
    Converte uma string YAML em dicionário Python.
    Usa fallback para extração via regex se YAML falhar.
    
    Args:
        yaml_content: String com conteúdo YAML
        
    Returns:
        Dicionário com os dados parseados ou None se falhar
    """
    # Tentar parsing YAML normal
    try:
        preprocessed = preprocess_yaml(yaml_content)
        return yaml.safe_load(preprocessed)
    except yaml.YAMLError:
        pass
    
    # Tentar sem preprocessing
    try:
        return yaml.safe_load(yaml_content)
    except yaml.YAMLError:
        pass
    
    # Fallback: extrair via regex
    result = extract_fields_via_regex(yaml_content)
    if result.get('Titulo'):
        return result
    
    return None


def extract_card_id(content: str, yaml_position: int) -> Optional[str]:
    """
    Extrai o ID do card a partir do cabeçalho antes do bloco YAML.
    
    Procura padrões como "### CARD EMP-001:" ou "## CARD BUS-001:"
    
    Args:
        content: Conteúdo completo do arquivo
        yaml_position: Posição onde o bloco YAML começa
        
    Returns:
        ID do card (ex: "EMP-001") ou None
    """
    text_before = content[:yaml_position]
    lines = text_before.split('\n')
    
    for line in reversed(lines[-10:]):
        # Suporta múltiplos formatos:
        # - GST-STR-001 (GESTOR)
        # - DEV-S1-001 (DEVS com sprint)
        # - STR-001 (formato simples)
        match = re.search(r'CARD\s+([A-Z]{2,4}-[A-Z0-9]{1,4}-\d{3}|[A-Z]{2,4}-\d{3})', line)
        if match:
            return match.group(1)
        
        match = re.search(r'##\s+([A-Z]{2,4}-[A-Z0-9]{1,4}-\d{3}|[A-Z]{2,4}-\d{3})', line)
        if match:
            return match.group(1)
    
    return None


def extract_hub_from_content(content: str, yaml_position: int) -> Optional[str]:
    """
    Extrai o Hub/seção do arquivo baseado nos cabeçalhos.
    
    Args:
        content: Conteúdo completo do arquivo
        yaml_position: Posição onde o bloco YAML começa
        
    Returns:
        Nome do Hub (ex: "empresa", "recrutamento") ou None
    """
    text_before = content[:yaml_position]
    
    hub_patterns = [
        (r'HUB\s+EMPRESA', 'empresa'),
        (r'HUB\s+RECRUTAMENTO', 'recrutamento'),
        (r'HUB\s+COMUNICACAO', 'comunicacao'),
        (r'HUB\s+PLANEJAMENTO', 'planejamento'),
        (r'HUB\s+METAS', 'planejamento'),  # legacy
        (r'HUB\s+BUSCA\s+GLOBAL', 'busca-global'),
        (r'TAB\s+BUSCA', 'busca'),
        (r'TAB\s+FAVORITOS', 'favoritos'),
        (r'TAB\s+LISTAS', 'listas'),
        (r'TAB\s+HISTORICO', 'historico'),
        (r'PORTFOLIO\s+DE\s+VAGAS', 'portfolio'),
        (r'CRIACAO\s+DE\s+VAGA', 'criacao-vaga'),
        (r'KANBAN', 'kanban'),
    ]
    
    for pattern, hub_name in hub_patterns:
        if re.search(pattern, text_before, re.IGNORECASE):
            return hub_name
    
    return None


def extract_full_content_from_yaml_block(yaml_content: str) -> str:
    """
    Extrai todo o conteúdo textual do bloco YAML para usar como descrição completa.
    Remove apenas os campos básicos de metadados e mantém todo o resto.
    
    Args:
        yaml_content: Conteúdo do bloco YAML
        
    Returns:
        Texto formatado com todo o conteúdo detalhado
    """
    lines = yaml_content.strip().split('\n')
    content_lines = []
    in_content = False
    skip_fields = {'Titulo', 'Tipo', 'Prioridade', 'Sprint', 'Pontos', 'Epic', 'Status', 
                   'Tempo', 'Ferramenta', 'Sequência', 'Dependências', 'Labels'}
    current_field = None
    
    for line in lines:
        # Verificar se é uma linha de campo de metadados básico
        field_match = re.match(r'^([A-Za-záéíóúÁÉÍÓÚçÇãõ\s]+):\s*(.*)$', line)
        
        if field_match:
            field_name = field_match.group(1).strip()
            if field_name in skip_fields:
                current_field = field_name
                continue
            else:
                current_field = None
                in_content = True
        
        if current_field in skip_fields:
            # Se a linha faz parte de um campo de metadados, pula
            if line.startswith('  ') or line.startswith('\t'):
                continue
            else:
                current_field = None
        
        # Adicionar linha ao conteúdo
        content_lines.append(line)
    
    return '\n'.join(content_lines)


def parse_markdown_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Processa um arquivo Markdown e extrai todos os cards.
    
    Args:
        file_path: Caminho para o arquivo .md
        
    Returns:
        Lista de cards com estrutura:
        {
            'id': 'EMP-001',
            'hub': 'empresa',
            'data': {...},  # Dados do YAML
            'source_file': 'configuracoes-admin-cards-jira.md'
        }
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    content = path.read_text(encoding='utf-8')
    cards = []
    
    pattern = r'```yaml\s*\n(.*?)```'
    for match in re.finditer(pattern, content, re.DOTALL):
        yaml_content = match.group(1)
        yaml_position = match.start()
        
        data = parse_yaml_block(yaml_content)
        if data is None:
            continue
        
        if 'Titulo' not in data and 'titulo' not in data:
            continue
        
        # Capturar TODO o conteúdo detalhado do bloco YAML
        full_content = extract_full_content_from_yaml_block(yaml_content)
        if full_content.strip():
            data['_full_content'] = full_content
        
        card_id = extract_card_id(content, yaml_position)
        hub = extract_hub_from_content(content, yaml_position)
        
        if card_id is None:
            titulo = data.get('Titulo', data.get('titulo', ''))
            # Suporta múltiplos formatos de ID
            match_id = re.search(r'\[?([A-Z]{2,4}-[A-Z0-9]{1,4}-\d{3}|[A-Z]{2,4}-\d{3})\]?', titulo)
            if match_id:
                card_id = match_id.group(1)
        
        if card_id is None:
            continue
        
        # Ignorar cards arquivados
        status = data.get('Status', data.get('status', ''))
        if status.upper() == 'ARQUIVADO':
            continue
        
        cards.append({
            'id': card_id,
            'hub': hub,
            'data': data,
            'source_file': path.name
        })
    
    return cards


def list_markdown_files(docs_path: str = 'docs') -> List[Path]:
    """
    Lista todos os arquivos .md com cards Jira no diretório docs.
    
    Args:
        docs_path: Caminho para a pasta de documentos
        
    Returns:
        Lista de Paths para arquivos .md com cards Jira
    """
    docs_dir = Path(docs_path)
    
    if not docs_dir.exists():
        return []
    
    jira_files = []
    
    for md_file in docs_dir.glob('**/*-cards-jira.md'):
        jira_files.append(md_file)
    
    for md_file in docs_dir.glob('**/*.md'):
        if md_file in jira_files:
            continue
        
        try:
            content = md_file.read_text(encoding='utf-8')
            if '```yaml' in content and ('Titulo:' in content or 'titulo:' in content):
                if re.search(r'CARD\s+[A-Z]{2,4}-\d{3}', content):
                    jira_files.append(md_file)
        except Exception:
            continue
    
    return sorted(jira_files)


if __name__ == '__main__':
    print("Arquivos .md com cards Jira encontrados:")
    print("-" * 50)
    
    for md_file in list_markdown_files():
        print(f"  {md_file}")
        
        try:
            cards = parse_markdown_file(str(md_file))
            print(f"    → {len(cards)} cards encontrados")
            
            for card in cards[:3]:
                titulo = card['data'].get('Titulo', card['data'].get('titulo', 'Sem título'))
                print(f"      • {card['id']}: {titulo[:50]}...")
            
            if len(cards) > 3:
                print(f"      ... e mais {len(cards) - 3} cards")
        except Exception as e:
            print(f"    → Erro: {e}")
        
        print()
