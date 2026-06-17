#!/usr/bin/env python3
"""
Script para fazer upload do documento de inventário para o Notion.
Usa a integração Replit Connector para autenticação.
"""

import os
import sys
import json
import httpx
from notion_client import Client

def get_notion_access_token():
    """Obtém o token de acesso do Notion via Replit Connector."""
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
    
    if repl_identity:
        x_replit_token = f'repl {repl_identity}'
    elif web_repl_renewal:
        x_replit_token = f'depl {web_repl_renewal}'
    else:
        raise Exception('X_REPLIT_TOKEN not found for repl/depl')
    
    if not hostname:
        raise Exception('REPLIT_CONNECTORS_HOSTNAME not set')
    
    response = httpx.get(
        f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=notion',
        headers={
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
    )
    
    data = response.json()
    connection = data.get('items', [{}])[0]
    
    settings = connection.get('settings', {})
    access_token = settings.get('access_token') or settings.get('oauth', {}).get('credentials', {}).get('access_token')
    
    if not access_token:
        raise Exception('Notion not connected or access token not found')
    
    return access_token


def markdown_to_notion_blocks(markdown_content: str) -> list:
    """Converte Markdown para blocos Notion (simplificado)."""
    blocks = []
    lines = markdown_content.split('\n')
    
    current_code_block = None
    code_language = 'plain text'
    
    for line in lines:
        if line.startswith('```'):
            if current_code_block is None:
                lang = line[3:].strip() or 'plain text'
                code_language = lang if lang else 'plain text'
                current_code_block = []
            else:
                code_text = '\n'.join(current_code_block)
                if code_text.strip():
                    text_chunks = [code_text[i:i+1900] for i in range(0, len(code_text), 1900)]
                    for chunk in text_chunks:
                        blocks.append({
                            "object": "block",
                            "type": "code",
                            "code": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}],
                                "language": code_language
                            }
                        })
                current_code_block = None
            continue
        
        if current_code_block is not None:
            current_code_block.append(line)
            continue
        
        if line.startswith('# '):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:].strip()[:2000]}}]
                }
            })
        elif line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": line[3:].strip()[:2000]}}]
                }
            })
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": line[4:].strip()[:2000]}}]
                }
            })
        elif line.startswith('> '):
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:].strip()[:2000]}}]
                }
            })
        elif line.startswith('- ') or line.startswith('* '):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:].strip()[:2000]}}]
                }
            })
        elif line.startswith('|') and '|' in line[1:]:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line[:2000]}}]
                }
            })
        elif line.strip() == '---':
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
        elif line.strip():
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line[:2000]}}]
                }
            })
    
    return blocks


def create_notion_page(notion: Client, parent_page_id: str, title: str, blocks: list):
    """Cria uma página no Notion."""
    MAX_BLOCKS_PER_REQUEST = 100
    
    new_page = notion.pages.create(
        parent={"page_id": parent_page_id},
        properties={
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        },
        children=blocks[:MAX_BLOCKS_PER_REQUEST]
    )
    
    page_id = new_page["id"]
    
    remaining_blocks = blocks[MAX_BLOCKS_PER_REQUEST:]
    while remaining_blocks:
        batch = remaining_blocks[:MAX_BLOCKS_PER_REQUEST]
        remaining_blocks = remaining_blocks[MAX_BLOCKS_PER_REQUEST:]
        notion.blocks.children.append(
            block_id=page_id,
            children=batch
        )
    
    return new_page


def find_or_create_parent_page(notion: Client) -> str:
    """Encontra uma página pai adequada no Notion ou usa a primeira disponível."""
    search_results = notion.search(
        query="WeDo Talent",
        filter={"property": "object", "value": "page"}
    )
    
    if search_results.get("results"):
        return search_results["results"][0]["id"]
    
    search_results = notion.search(
        query="Documentação",
        filter={"property": "object", "value": "page"}
    )
    
    if search_results.get("results"):
        return search_results["results"][0]["id"]
    
    search_results = notion.search(
        filter={"property": "object", "value": "page"}
    )
    
    if search_results.get("results"):
        return search_results["results"][0]["id"]
    
    raise Exception("Nenhuma página encontrada no Notion para usar como pai")


def main():
    print("Conectando ao Notion via Replit Connector...")
    
    try:
        access_token = get_notion_access_token()
        print("Token obtido com sucesso!")
    except Exception as e:
        print(f"Erro ao obter token: {e}")
        sys.exit(1)
    
    notion = Client(auth=access_token)
    
    print("Lendo documento...")
    doc_path = "docs/WEDOTALENT_INTEGRACOES_COMPLETO.md"
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Documento lido: {len(content)} caracteres")
    
    print("Convertendo para blocos Notion...")
    blocks = markdown_to_notion_blocks(content)
    print(f"Convertido para {len(blocks)} blocos")
    
    print("Buscando página pai no Notion...")
    try:
        parent_id = find_or_create_parent_page(notion)
        print(f"Página pai encontrada: {parent_id}")
    except Exception as e:
        print(f"Erro ao buscar página pai: {e}")
        sys.exit(1)
    
    print("Criando página no Notion...")
    try:
        new_page = create_notion_page(
            notion,
            parent_id,
            "WeDo Talent - Guia Completo de Integrações e Arquitetura",
            blocks
        )
        
        page_url = new_page.get("url", "URL não disponível")
        print(f"\nPágina criada com sucesso!")
        print(f"URL: {page_url}")
        
    except Exception as e:
        print(f"Erro ao criar página: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
