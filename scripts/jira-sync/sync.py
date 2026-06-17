#!/usr/bin/env python3
"""
CLI para sincronização de cards do Jira a partir de arquivos Markdown.

Uso:
    python sync.py list                          # Lista arquivos .md disponíveis
    python sync.py preview <arquivo.md>          # Preview do que será sincronizado
    python sync.py sync <arquivo.md>             # Sincroniza com confirmação
    python sync.py sync <arquivo.md> --yes       # Sincroniza sem perguntar
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Aviso: 'rich' não instalado. Output será simplificado.")
    print("Instale com: pip install rich")

from parser import parse_markdown_file, list_markdown_files
from converter import convert_card_to_jira
from jira_client import JiraClient, JiraAPIError, check_credentials


if RICH_AVAILABLE:
    console = Console()


def print_error(message: str):
    """Imprime mensagem de erro."""
    if RICH_AVAILABLE:
        console.print(f"[red]✗ {message}[/red]")
    else:
        print(f"ERRO: {message}")


def print_success(message: str):
    """Imprime mensagem de sucesso."""
    if RICH_AVAILABLE:
        console.print(f"[green]✓ {message}[/green]")
    else:
        print(f"OK: {message}")


def print_warning(message: str):
    """Imprime mensagem de aviso."""
    if RICH_AVAILABLE:
        console.print(f"[yellow]⚠ {message}[/yellow]")
    else:
        print(f"AVISO: {message}")


def print_info(message: str):
    """Imprime mensagem informativa."""
    if RICH_AVAILABLE:
        console.print(f"[blue]ℹ {message}[/blue]")
    else:
        print(f"INFO: {message}")


def cmd_list(args):
    """Lista arquivos .md com cards Jira."""
    docs_path = args.docs_path
    
    print_info(f"Buscando arquivos em: {docs_path}/")
    print()
    
    md_files = list_markdown_files(docs_path)
    
    if not md_files:
        print_warning("Nenhum arquivo .md com cards Jira encontrado.")
        return
    
    if RICH_AVAILABLE:
        table = Table(title="Arquivos com Cards Jira")
        table.add_column("Arquivo", style="cyan")
        table.add_column("Cards", justify="right", style="green")
        table.add_column("Caminho", style="dim")
        
        total_cards = 0
        for md_file in md_files:
            try:
                cards = parse_markdown_file(str(md_file))
                count = len(cards)
                total_cards += count
                table.add_row(md_file.name, str(count), str(md_file.parent))
            except Exception as e:
                table.add_row(md_file.name, "[red]Erro[/red]", str(e)[:50])
        
        console.print(table)
        print()
        print_info(f"Total: {len(md_files)} arquivos, {total_cards} cards")
    else:
        print("Arquivos encontrados:")
        total_cards = 0
        for md_file in md_files:
            try:
                cards = parse_markdown_file(str(md_file))
                count = len(cards)
                total_cards += count
                print(f"  {md_file.name}: {count} cards")
            except Exception as e:
                print(f"  {md_file.name}: ERRO - {e}")
        print(f"\nTotal: {len(md_files)} arquivos, {total_cards} cards")


def analyze_cards(cards: List[Dict[str, Any]], client: JiraClient) -> Tuple[List, List]:
    """
    Analisa cards para determinar quais são novos e quais existem.
    
    Returns:
        Tupla (cards_novos, cards_existentes)
    """
    new_cards = []
    existing_cards = []
    
    if RICH_AVAILABLE:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analisando cards...", total=len(cards))
            
            for card in cards:
                existing = client.find_issue_by_card_id(card['id'])
                
                if existing:
                    existing_cards.append({
                        'card': card,
                        'issue': existing
                    })
                else:
                    new_cards.append(card)
                
                progress.advance(task)
    else:
        for i, card in enumerate(cards):
            print(f"\r  Analisando {i+1}/{len(cards)}...", end="")
            existing = client.find_issue_by_card_id(card['id'])
            
            if existing:
                existing_cards.append({
                    'card': card,
                    'issue': existing
                })
            else:
                new_cards.append(card)
        print()
    
    return new_cards, existing_cards


def cmd_preview(args):
    """Mostra preview do que será sincronizado."""
    file_path = args.file
    
    if not Path(file_path).exists():
        print_error(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)
    
    creds = check_credentials()
    if not creds['JIRA_EMAIL'] or not creds['JIRA_API_TOKEN']:
        print_error("Credenciais do Jira não configuradas.")
        print_info("Configure JIRA_EMAIL e JIRA_API_TOKEN como variáveis de ambiente.")
        sys.exit(1)
    
    print_info(f"Parseando arquivo: {file_path}")
    
    try:
        cards = parse_markdown_file(file_path)
    except Exception as e:
        print_error(f"Erro ao parsear arquivo: {e}")
        sys.exit(1)
    
    if not cards:
        print_warning("Nenhum card encontrado no arquivo.")
        return
    
    print_success(f"{len(cards)} cards encontrados")
    print()
    
    try:
        client = JiraClient()
        
        if not client.test_connection():
            print_error("Falha na conexão com o Jira.")
            sys.exit(1)
        
        print_success("Conexão com Jira OK")
        print()
        
    except (ValueError, JiraAPIError) as e:
        print_error(f"Erro ao conectar ao Jira: {e}")
        sys.exit(1)
    
    new_cards, existing_cards = analyze_cards(cards, client)
    
    if RICH_AVAILABLE:
        if new_cards:
            console.print(Panel(f"[green]{len(new_cards)} cards NOVOS[/green] (serão criados)", title="Novos"))
            
            table = Table()
            table.add_column("ID", style="cyan")
            table.add_column("Título")
            table.add_column("Tipo", style="dim")
            table.add_column("Pontos", justify="right")
            
            for card in new_cards:
                data = card['data']
                titulo = data.get('Titulo', data.get('titulo', ''))[:50]
                tipo = data.get('Tipo', 'Story')
                pontos = str(data.get('Pontos', '-'))
                table.add_row(card['id'], titulo, tipo, pontos)
            
            console.print(table)
            print()
        
        if existing_cards:
            console.print(Panel(f"[yellow]{len(existing_cards)} cards EXISTENTES[/yellow] (serão atualizados)", title="Existentes"))
            
            table = Table()
            table.add_column("ID", style="cyan")
            table.add_column("Issue Jira", style="green")
            table.add_column("Status Atual", style="dim")
            
            for item in existing_cards:
                card = item['card']
                issue = item['issue']
                issue_key = issue['key']
                status = issue['fields']['status']['name']
                table.add_row(card['id'], issue_key, status)
            
            console.print(table)
            print()
        
        console.print(Panel(
            f"[green]Novos: {len(new_cards)}[/green]  |  "
            f"[yellow]Existentes: {len(existing_cards)}[/yellow]  |  "
            f"[blue]Total: {len(cards)}[/blue]",
            title="Resumo"
        ))
    else:
        print(f"\n=== PREVIEW ===")
        print(f"Cards novos (serão criados): {len(new_cards)}")
        for card in new_cards:
            titulo = card['data'].get('Titulo', '')[:40]
            print(f"  + {card['id']}: {titulo}")
        
        print(f"\nCards existentes (serão atualizados): {len(existing_cards)}")
        for item in existing_cards:
            print(f"  ~ {item['card']['id']} → {item['issue']['key']}")
        
        print(f"\nTotal: {len(cards)} cards")


def cmd_sync(args):
    """Sincroniza cards com o Jira."""
    file_path = args.file
    auto_yes = args.yes
    
    if not Path(file_path).exists():
        print_error(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)
    
    creds = check_credentials()
    if not creds['JIRA_EMAIL'] or not creds['JIRA_API_TOKEN']:
        print_error("Credenciais do Jira não configuradas.")
        print_info("Configure JIRA_EMAIL e JIRA_API_TOKEN como variáveis de ambiente.")
        sys.exit(1)
    
    print_info(f"Parseando arquivo: {file_path}")
    
    try:
        cards = parse_markdown_file(file_path)
    except Exception as e:
        print_error(f"Erro ao parsear arquivo: {e}")
        sys.exit(1)
    
    if not cards:
        print_warning("Nenhum card encontrado no arquivo.")
        return
    
    print_success(f"{len(cards)} cards encontrados")
    
    try:
        client = JiraClient()
        
        if not client.test_connection():
            print_error("Falha na conexão com o Jira.")
            sys.exit(1)
        
        print_success("Conexão com Jira OK")
        print()
        
    except (ValueError, JiraAPIError) as e:
        print_error(f"Erro ao conectar ao Jira: {e}")
        sys.exit(1)
    
    new_cards, existing_cards = analyze_cards(cards, client)
    
    print()
    print_info(f"Cards novos: {len(new_cards)}")
    print_info(f"Cards existentes: {len(existing_cards)}")
    print()
    
    if not new_cards and not existing_cards:
        print_warning("Nenhum card para sincronizar.")
        return
    
    if not auto_yes:
        if RICH_AVAILABLE:
            proceed = Confirm.ask("Deseja prosseguir com a sincronização?")
        else:
            response = input("Deseja prosseguir com a sincronização? (s/N): ")
            proceed = response.lower() in ['s', 'sim', 'y', 'yes']
        
        if not proceed:
            print_warning("Sincronização cancelada.")
            return
    
    created = []
    updated = []
    errors = []
    
    if new_cards:
        print()
        print_info("Criando cards novos...")
        
        for card in new_cards:
            try:
                payload = convert_card_to_jira(card, project_key=client.project_key)
                result = client.create_issue(payload)
                issue_key = result['key']
                
                client.move_to_todo(issue_key)
                
                created.append({
                    'card_id': card['id'],
                    'issue_key': issue_key,
                    'url': client.get_issue_url(issue_key)
                })
                
                print_success(f"  {card['id']} → {issue_key}")
                
            except JiraAPIError as e:
                errors.append({
                    'card_id': card['id'],
                    'error': str(e)
                })
                print_error(f"  {card['id']}: {e}")
    
    if existing_cards:
        print()
        print_info("Atualizando cards existentes...")
        
        for item in existing_cards:
            card = item['card']
            issue = item['issue']
            issue_key = issue['key']
            
            try:
                payload = convert_card_to_jira(card, project_key=client.project_key)
                del payload['fields']['project']
                del payload['fields']['issuetype']
                
                client.update_issue(issue_key, payload)
                
                updated.append({
                    'card_id': card['id'],
                    'issue_key': issue_key,
                    'url': client.get_issue_url(issue_key)
                })
                
                print_success(f"  {card['id']} → {issue_key} (atualizado)")
                
            except JiraAPIError as e:
                errors.append({
                    'card_id': card['id'],
                    'error': str(e)
                })
                print_error(f"  {card['id']}: {e}")
    
    print()
    print("=" * 60)
    print_info("RESULTADO DA SINCRONIZAÇÃO")
    print("=" * 60)
    print()
    
    if created:
        print_success(f"Cards criados: {len(created)}")
        for item in created:
            print(f"  • {item['card_id']} → {item['url']}")
    
    if updated:
        print_success(f"Cards atualizados: {len(updated)}")
        for item in updated:
            print(f"  • {item['card_id']} → {item['url']}")
    
    if errors:
        print()
        print_error(f"Erros: {len(errors)}")
        for item in errors:
            print(f"  • {item['card_id']}: {item['error']}")
    
    print()
    
    if errors:
        sys.exit(1)


def main():
    """Função principal do CLI."""
    parser = argparse.ArgumentParser(
        description='Sincroniza cards de arquivos Markdown com o Jira',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python sync.py list                          Lista arquivos .md disponíveis
  python sync.py preview docs/cards.md         Preview do que será sincronizado
  python sync.py sync docs/cards.md            Sincroniza com confirmação
  python sync.py sync docs/cards.md --yes      Sincroniza sem perguntar

Variáveis de ambiente necessárias:
  JIRA_EMAIL         Email da conta Jira
  JIRA_API_TOKEN     Token de API do Jira
  JIRA_BASE_URL      URL base (default: https://wedotalent.atlassian.net)
  JIRA_PROJECT_KEY   Chave do projeto (default: WT)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    list_parser = subparsers.add_parser('list', help='Lista arquivos .md com cards')
    list_parser.add_argument(
        '--docs-path', '-d',
        default='docs',
        help='Caminho para pasta de documentos (default: docs)'
    )
    
    preview_parser = subparsers.add_parser('preview', help='Preview do que será sincronizado')
    preview_parser.add_argument('file', help='Arquivo .md para processar')
    
    sync_parser = subparsers.add_parser('sync', help='Sincroniza cards com o Jira')
    sync_parser.add_argument('file', help='Arquivo .md para sincronizar')
    sync_parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Sincroniza sem pedir confirmação'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    if args.command == 'list':
        cmd_list(args)
    elif args.command == 'preview':
        cmd_preview(args)
    elif args.command == 'sync':
        cmd_sync(args)


if __name__ == '__main__':
    main()
