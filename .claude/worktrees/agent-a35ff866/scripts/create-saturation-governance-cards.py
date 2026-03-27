#!/usr/bin/env python3
"""
Script para criar cards de Saturacao, Governanca e Calibracao no Jira.
Projeto: WeDoTalent Tasks 2026 Ref WT
Coluna: Vagas
"""

import os
import json
import time
import requests

NEW_CARDS = [
    {
        "id": "VAG-123",
        "titulo": "[FRONT] Badge Pipeline Saturado - Indicador Visual",
        "points": 5,
        "prioridade": "High",
        "categoria": "Frontend",
        "epic": "EPIC-VAG-012",
        "descricao": "Implementar badge visual no header do pipeline de candidatos que indica quando o pipeline atingiu o limite de candidatos aprovados (saturacao). Estados: Saturado (vermelho), Proximo (amarelo), Normal (verde)."
    },
    {
        "id": "VAG-124",
        "titulo": "[FRONT] Botao Desbloquear Pipeline - Override Manual",
        "points": 5,
        "prioridade": "High",
        "categoria": "Frontend",
        "epic": "EPIC-VAG-012",
        "descricao": "Botao que permite ao recrutador desbloquear manualmente o pipeline saturado, aumentando o threshold ou retomando a triagem automatica. Modal de confirmacao com opcoes."
    },
    {
        "id": "VAG-125",
        "titulo": "[BACK-IA] API GET /saturation-status",
        "points": 5,
        "prioridade": "Highest",
        "categoria": "Backend-IA",
        "epic": "EPIC-VAG-012",
        "descricao": "Endpoint que retorna status atual de saturacao do pipeline de uma vaga especifica. Response: approved_count, saturation_threshold, is_saturated, slots_remaining, recommendation."
    },
    {
        "id": "VAG-126",
        "titulo": "[BACK-IA] API POST /unlock-pipeline",
        "points": 5,
        "prioridade": "High",
        "categoria": "Backend-IA",
        "epic": "EPIC-VAG-012",
        "descricao": "Endpoint que desbloqueia pipeline saturado, aumentando threshold ou desativando temporariamente. Registra audit log e notifica sistema de triagem."
    },
    {
        "id": "VAG-127",
        "titulo": "[FRONT] Wizard Step 7.5 - Configuracao GovernanceRules",
        "points": 8,
        "prioridade": "High",
        "categoria": "Frontend",
        "epic": "EPIC-VAG-012",
        "descricao": "Nova etapa no wizard de criacao de vaga para configurar as regras de autonomia da LIA (GovernanceRules). Campos: auto_schedule_interviews, auto_send_negative_feedback, allow_ai_first_contact, saturation_threshold."
    },
    {
        "id": "VAG-128",
        "titulo": "[FRONT] GovernanceRulesForm - Componente Reutilizavel",
        "points": 5,
        "prioridade": "High",
        "categoria": "Frontend",
        "epic": "EPIC-VAG-012",
        "descricao": "Componente de formulario reutilizavel para configurar GovernanceRules, usado no wizard e na edicao de vaga. Switches e NumberInputs para cada regra."
    },
    {
        "id": "VAG-129",
        "titulo": "[FRONT] LIAFeedbackWidget - Thumbs Up/Down",
        "points": 5,
        "prioridade": "High",
        "categoria": "Frontend",
        "epic": "EPIC-VAG-012",
        "descricao": "Widget de feedback para cada recomendacao da LIA, permitindo thumbs up/down para calibracao. Modal de razao quando disagree. API: POST /calibration/feedback."
    },
    {
        "id": "VAG-130",
        "titulo": "[FRONT] CalibrationInsights - Painel de Divergencias",
        "points": 8,
        "prioridade": "Medium",
        "categoria": "Frontend",
        "epic": "EPIC-VAG-012",
        "descricao": "Painel que mostra divergencias entre LIA e recrutador nos ultimos 30 dias, com opcao de aprovar ajustes. Taxa de concordancia, sugestoes de ajuste de pesos."
    },
    {
        "id": "VAG-131",
        "titulo": "[BACK-IA] API POST /calibration/feedback",
        "points": 5,
        "prioridade": "Highest",
        "categoria": "Backend-IA",
        "epic": "EPIC-VAG-012",
        "descricao": "Endpoint para registrar feedback explicito do recrutador sobre recomendacoes da LIA. Request: candidate_id, job_id, agrees_with_lia, lia_score, feedback_reason. Status: Implementado."
    },
    {
        "id": "VAG-132",
        "titulo": "[BACK-IA] API GET /calibration/divergences",
        "points": 8,
        "prioridade": "High",
        "categoria": "Backend-IA",
        "epic": "EPIC-VAG-012",
        "descricao": "Endpoint que retorna divergencias entre LIA e recrutador nos ultimos 30 dias. Response: divergences[], total_divergences, agreement_rate, suggestions[]. Status: Implementado."
    },
]


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


def get_project_info(access_token, cloud_id):
    """Get project key for WeDoTalent Tasks 2026"""
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/search'
    
    response = requests.get(
        url,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
    )
    
    if response.status_code == 200:
        projects = response.json().get('values', [])
        for project in projects:
            if 'WT' in project['key'] or 'wedotalent' in project['name'].lower():
                print(f"Found project: {project['name']} ({project['key']})")
                return project['key']
    
    return None


def create_jira_issue(access_token, cloud_id, project_key, card):
    url = f'https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue'
    
    labels = ['Vagas', card['categoria'], card['epic']]
    if 'IA' in card['categoria']:
        labels.append('Backend-IA')
    
    fields = {
        'project': {'key': project_key},
        'summary': f"{card['id']}: {card['titulo']}",
        'description': {
            'type': 'doc',
            'version': 1,
            'content': [
                {
                    'type': 'paragraph',
                    'content': [
                        {'type': 'text', 'text': card['descricao']}
                    ]
                },
                {
                    'type': 'paragraph',
                    'content': [
                        {'type': 'text', 'text': f"Epic: {card['epic']}"}
                    ]
                },
                {
                    'type': 'paragraph',
                    'content': [
                        {'type': 'text', 'text': f"Story Points: {card['points']}"}
                    ]
                }
            ]
        },
        'issuetype': {'name': 'Task'},
        'labels': labels,
    }
    
    try:
        response = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json={'fields': fields}
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Created: {card['id']} -> {result['key']}")
            return {'success': True, 'key': result['key'], 'id': card['id']}
        else:
            print(f"❌ Failed: {card['id']} - {response.status_code}: {response.text}")
            return {'success': False, 'id': card['id'], 'error': response.text}
    
    except Exception as e:
        print(f"❌ Error: {card['id']} - {str(e)}")
        return {'success': False, 'id': card['id'], 'error': str(e)}


def main():
    print("=" * 60)
    print("Criando cards de Saturacao, Governanca e Calibracao no Jira")
    print("=" * 60)
    
    try:
        access_token, cloud_id = get_jira_credentials()
        print(f"✅ Conectado ao Jira (Cloud ID: {cloud_id[:8]}...)")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    project_key = get_project_info(access_token, cloud_id)
    if not project_key:
        project_key = 'WT'
        print(f"⚠️ Usando projeto padrao: {project_key}")
    
    print(f"\n📋 Criando {len(NEW_CARDS)} cards no projeto {project_key}...")
    print("-" * 60)
    
    results = []
    for card in NEW_CARDS:
        result = create_jira_issue(access_token, cloud_id, project_key, card)
        results.append(result)
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    
    success = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"✅ Criados: {len(success)}")
    print(f"❌ Falhas: {len(failed)}")
    
    if success:
        print("\nCards criados:")
        for r in success:
            print(f"  - {r['id']} -> {r['key']}")
    
    if failed:
        print("\nCards com falha:")
        for r in failed:
            print(f"  - {r['id']}: {r.get('error', 'Unknown error')[:100]}")
    
    with open('scripts/saturation-governance-cards-result.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Resultados salvos em scripts/saturation-governance-cards-result.json")


if __name__ == '__main__':
    main()
