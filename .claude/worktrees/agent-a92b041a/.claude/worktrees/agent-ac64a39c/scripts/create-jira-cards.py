#!/usr/bin/env python3
"""
Script para extrair cards do documento de Gestão de Vagas e criar no Jira.
"""

import re
import json

CARDS_DATA = [
    {"id": "VAG-001", "titulo": "Header Principal Gestao de Vagas", "points": 3, "prioridade": "High"},
    {"id": "VAG-002", "titulo": "Botao Nova Vaga", "points": 5, "prioridade": "Highest"},
    {"id": "VAG-003", "titulo": "Integracao Busca Global", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-004", "titulo": "Integracao Notificacoes", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-005", "titulo": "Sistema de Tabs de Filtro", "points": 8, "prioridade": "High"},
    {"id": "VAG-006", "titulo": "Contadores Dinamicos por Status", "points": 5, "prioridade": "High"},
    {"id": "VAG-007", "titulo": "Filtro Todas as Vagas", "points": 3, "prioridade": "High"},
    {"id": "VAG-008", "titulo": "Filtro Vagas Ativas", "points": 3, "prioridade": "High"},
    {"id": "VAG-009", "titulo": "Filtro Vagas Urgentes", "points": 5, "prioridade": "High"},
    {"id": "VAG-010", "titulo": "Filtro Vagas Paralisadas", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-011", "titulo": "Filtro Concluidas e Canceladas", "points": 3, "prioridade": "Low"},
    {"id": "VAG-012", "titulo": "Container LIA Centralizado", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-013", "titulo": "Titulo Contextual Dinamico", "points": 3, "prioridade": "High"},
    {"id": "VAG-014", "titulo": "Input de Chat LIA", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-015", "titulo": "Icones Microfone e Busca", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-016", "titulo": "Sugestoes Contextuais", "points": 8, "prioridade": "High"},
    {"id": "VAG-017", "titulo": "Integracao Backend LIA", "points": 13, "prioridade": "Highest"},
    {"id": "VAG-018", "titulo": "Acao Criar Nova Vaga", "points": 5, "prioridade": "Highest"},
    {"id": "VAG-019", "titulo": "Acao Ver Minhas Vagas", "points": 3, "prioridade": "High"},
    {"id": "VAG-020", "titulo": "Acao Ver Todas as Vagas", "points": 3, "prioridade": "High"},
    {"id": "VAG-021", "titulo": "Acao Resumo das Vagas", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-022", "titulo": "Acao Mais Ideias (AI)", "points": 8, "prioridade": "Medium"},
    {"id": "VAG-023", "titulo": "Empty State Design", "points": 5, "prioridade": "High"},
    {"id": "VAG-024", "titulo": "Mensagem Boas-Vindas LIA", "points": 3, "prioridade": "High"},
    {"id": "VAG-028", "titulo": "Tabela de Vagas - Estrutura Base", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-029", "titulo": "Colunas Configuraveis Toggle/Order", "points": 5, "prioridade": "High"},
    {"id": "VAG-030", "titulo": "Ordenacao Multi-Coluna Sort", "points": 3, "prioridade": "High"},
    {"id": "VAG-031", "titulo": "Redimensionamento de Colunas", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-032", "titulo": "Selecao em Lote Checkbox", "points": 5, "prioridade": "High"},
    {"id": "VAG-033", "titulo": "Persistencia de Config localStorage", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-034", "titulo": "Coluna Performance LIA Triagens", "points": 5, "prioridade": "High"},
    {"id": "VAG-035", "titulo": "Coluna Roteiro de Triagem", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-036", "titulo": "Acoes por Linha Menu Dropdown", "points": 5, "prioridade": "High"},
    {"id": "VAG-037", "titulo": "Preview Panel - Estrutura Base", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-038", "titulo": "Tab Visao Geral - Funil Rapido", "points": 5, "prioridade": "High"},
    {"id": "VAG-039", "titulo": "Tab Visao Geral - Metricas LIA", "points": 5, "prioridade": "High"},
    {"id": "VAG-040", "titulo": "Tab Visao Geral - Responsaveis", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-041", "titulo": "Tab Visao Geral - Datas Criticas", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-042", "titulo": "Tab Roteiro de Triagem - WSI Blocks", "points": 13, "prioridade": "Highest"},
    {"id": "VAG-043", "titulo": "WSI Blocks - Accordion Expansivel", "points": 5, "prioridade": "High"},
    {"id": "VAG-044", "titulo": "WSI Blocks - Editor de Perguntas", "points": 8, "prioridade": "High"},
    {"id": "VAG-045", "titulo": "Configuracao de Canais de Triagem", "points": 5, "prioridade": "High"},
    {"id": "VAG-046", "titulo": "Processo Seletivo Inline Breadcrumb", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-047", "titulo": "Resize do Painel de Preview", "points": 3, "prioridade": "Low"},
    {"id": "VAG-048", "titulo": "JobActionsBar - Barra de Acoes", "points": 5, "prioridade": "High"},
    {"id": "VAG-049", "titulo": "JobPublishModal - Publicar em Canais", "points": 8, "prioridade": "High"},
    {"id": "VAG-050", "titulo": "JobInsightsModal - Metricas Expandidas", "points": 13, "prioridade": "Highest"},
    {"id": "VAG-051", "titulo": "JobDuplicateModal - Duplicar Vaga", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-052", "titulo": "JobStatusModal - Pausar/Ativar Vaga", "points": 5, "prioridade": "High"},
    {"id": "VAG-053", "titulo": "JobAssignRecruiterModal - Atribuir Recrutador", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-054", "titulo": "JobUnpublishModal - Despublicar Vaga", "points": 5, "prioridade": "Low"},
    {"id": "VAG-055", "titulo": "JobCompareModal - Comparar Vagas", "points": 8, "prioridade": "Medium"},
    {"id": "VAG-056", "titulo": "EditJobModal - Edicao Completa", "points": 13, "prioridade": "Highest"},
    {"id": "VAG-057", "titulo": "JobFiltersPanel - Painel Lateral", "points": 8, "prioridade": "High"},
    {"id": "VAG-058", "titulo": "Filtros Rapidos Ativas/Urgentes/Remotas", "points": 3, "prioridade": "High"},
    {"id": "VAG-059", "titulo": "Filtro por Status da Vaga", "points": 3, "prioridade": "High"},
    {"id": "VAG-060", "titulo": "Filtro por Etapa do Processo", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-061", "titulo": "Filtro por Modelo de Trabalho", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-062", "titulo": "Filtro por Recrutador/Gestor", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-063", "titulo": "Busca Booleana AND/OR/NOT", "points": 5, "prioridade": "Low"},
    {"id": "VAG-064", "titulo": "Pesquisas Salvas Templates", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-065", "titulo": "Persistencia de Filtros Hook", "points": 3, "prioridade": "High"},
    {"id": "VAG-066", "titulo": "Nivel 1 Mini Prompt Inline", "points": 5, "prioridade": "High"},
    {"id": "VAG-067", "titulo": "Nivel 2 Chat Expandido Lateral", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-068", "titulo": "Nivel 3 Super Chat Criacao de Vaga", "points": 13, "prioridade": "Highest"},
    {"id": "VAG-069", "titulo": "Deteccao de Intent de Criacao", "points": 5, "prioridade": "High"},
    {"id": "VAG-070", "titulo": "Auto-Expand LIA ao Selecionar Vagas", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-071", "titulo": "Historico de Mensagens Inline", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-072", "titulo": "AudioRecordButton Gravacao de Voz", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-073", "titulo": "LiaVacancyQueriesGuide Popover", "points": 5, "prioridade": "High"},
    {"id": "VAG-074", "titulo": "ExpandedChatModal Modal Full", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-075", "titulo": "Botao Nova Vaga Header", "points": 3, "prioridade": "High"},
    {"id": "VAG-076", "titulo": "Super Chat Modal Container", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-077", "titulo": "Wizard Step 1 Descricao Inicial", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-078", "titulo": "Wizard Step 2 Informacoes Basicas", "points": 5, "prioridade": "High"},
    {"id": "VAG-079", "titulo": "Wizard Step 3 Remuneracao e Beneficios", "points": 5, "prioridade": "High"},
    {"id": "VAG-080", "titulo": "Wizard Step 4 Competencias Tecnicas", "points": 8, "prioridade": "High"},
    {"id": "VAG-081", "titulo": "Wizard Step 5 Competencias WSI", "points": 8, "prioridade": "High"},
    {"id": "VAG-082", "titulo": "Wizard Step 6 Requisitos Idiomas", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-083", "titulo": "Wizard Step 7 Scorecard Avaliacao", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-084", "titulo": "Wizard Step 8 Prazos e Cronograma", "points": 5, "prioridade": "High"},
    {"id": "VAG-085", "titulo": "Wizard Step 9 Pipeline do Processo", "points": 8, "prioridade": "High"},
    {"id": "VAG-086", "titulo": "Wizard Step 10 Solicitacao de Dados", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-087", "titulo": "Wizard Step 11 Revisao Final", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-088", "titulo": "[BACK] Endpoint /lia/job-wizard/step", "points": 13, "prioridade": "Highest"},
    {"id": "VAG-089", "titulo": "Navegacao entre Etapas Stepper", "points": 5, "prioridade": "High"},
    {"id": "VAG-090", "titulo": "Calibracao de Candidatos Sourcing", "points": 8, "prioridade": "High"},
    {"id": "VAG-091", "titulo": "ScreeningQuestionsPanel Perguntas", "points": 8, "prioridade": "High"},
    {"id": "VAG-092", "titulo": "Integracao com Busca Global Pearch", "points": 8, "prioridade": "High"},
    {"id": "VAG-093", "titulo": "Validacao de Dados Zod Schema", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-094", "titulo": "[BACK-RAILS] API CRUD Vagas", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-095", "titulo": "[BACK-RAILS] API Filtros Avancados", "points": 5, "prioridade": "High"},
    {"id": "VAG-096", "titulo": "[BACK-RAILS] API Publicacao Multi-Canal", "points": 8, "prioridade": "High"},
    {"id": "VAG-097", "titulo": "[BACK-RAILS] API Metricas Vaga", "points": 5, "prioridade": "High"},
    {"id": "VAG-098", "titulo": "[BACK-RAILS] API Duplicacao Vaga", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-099", "titulo": "[BACK-RAILS] API Status Vaga", "points": 3, "prioridade": "High"},
    {"id": "VAG-100", "titulo": "[BACK-RAILS] API Atribuicao Recrutador", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-101", "titulo": "[BACK-RAILS] API Comparacao Vagas", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-102", "titulo": "[BACK-RAILS] Webhooks Mudanca Status", "points": 5, "prioridade": "High"},
    {"id": "VAG-103", "titulo": "[BACK-RAILS] API Pesquisas Salvas", "points": 3, "prioridade": "Medium"},
    {"id": "VAG-104", "titulo": "[BACK-RAILS] API Usuarios Recrutadores", "points": 5, "prioridade": "High"},
    {"id": "VAG-105", "titulo": "[BACK-RAILS] API Pipeline Stages", "points": 5, "prioridade": "High"},
    {"id": "VAG-106", "titulo": "[BACK-RAILS] API Integracao WorkOS", "points": 8, "prioridade": "High"},
    {"id": "VAG-107", "titulo": "[BACK-RAILS] API Logs Auditoria", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-108", "titulo": "[BACK-RAILS] API Export PDF/CSV", "points": 5, "prioridade": "Medium"},
    {"id": "VAG-109", "titulo": "[BACK-IA] Comparacao de Candidatos por Cenario", "points": 13, "prioridade": "Highest"},
    {"id": "VAG-110", "titulo": "[BACK-IA] Score LIA Unificado", "points": 8, "prioridade": "Highest"},
    {"id": "VAG-111", "titulo": "[BACK-IA] Parecer Automatico de Candidato", "points": 8, "prioridade": "High"},
    {"id": "VAG-112", "titulo": "[BACK-IA] Metodologia LIA Unificada", "points": 5, "prioridade": "High"},
    {"id": "VAG-113", "titulo": "[BACK-IA] WSI Scoped por VacancyCandidate", "points": 5, "prioridade": "High"},
    {"id": "VAG-114", "titulo": "[BACK-IA] Testes de Validacao Cenarios", "points": 5, "prioridade": "High"},
    {"id": "VAG-115", "titulo": "[BACK-IA] WSI Service - Metodologia Cientifica", "points": 13, "prioridade": "Highest"},
    {"id": "VAG-116", "titulo": "[BACK-IA] CV Parser - Extracao Inteligente", "points": 8, "prioridade": "High"},
    {"id": "VAG-117", "titulo": "[BACK-IA] WSI Question Generator", "points": 8, "prioridade": "High"},
    {"id": "VAG-118", "titulo": "[BACK-IA] Personalized Feedback Service", "points": 8, "prioridade": "Medium"},
    {"id": "VAG-119", "titulo": "[BACK-IA] Culture Analyzer Service", "points": 8, "prioridade": "Medium"},
    {"id": "VAG-120", "titulo": "[BACK-IA] Interview Transcript Analysis", "points": 13, "prioridade": "High"},
    {"id": "VAG-121", "titulo": "[BACK-IA] Semantic Search Service", "points": 8, "prioridade": "High"},
    {"id": "VAG-122", "titulo": "[BACK-IA] Candidate Enrichment Service", "points": 8, "prioridade": "Medium"},
]

def convert_to_jira_issues(cards, project_key):
    issues = []
    for card in cards:
        labels = ["VAGAS"]
        
        if "[BACK-IA]" in card["titulo"]:
            labels.append("Backend-IA")
        elif "[BACK-RAILS]" in card["titulo"] or "[BACK]" in card["titulo"]:
            labels.append("Backend")
        else:
            labels.append("Frontend")
        
        issues.append({
            "projectKey": project_key,
            "summary": f"[{card['id']}] {card['titulo']}",
            "description": f"Card da documentacao de Gestao de Vagas.\n\nID: {card['id']}\nStory Points: {card['points']}\nPrioridade: {card['prioridade']}",
            "issueType": "Task",
            "labels": labels,
            "priority": card["prioridade"],
        })
    
    return issues

def main():
    project_key = "WT"
    issues = convert_to_jira_issues(CARDS_DATA, project_key)
    
    output = {
        "action": "create-bulk",
        "issues": issues
    }
    
    with open("scripts/jira-issues-payload.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(issues)} issues for Jira")
    print(f"Saved to scripts/jira-issues-payload.json")
    print("\nFirst 5 issues:")
    for issue in issues[:5]:
        print(f"  - {issue['summary']}")

if __name__ == "__main__":
    main()
