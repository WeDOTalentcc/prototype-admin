# LIA Agent x Tools x Prompts Map

## Summary
- **Total Agents:** 20
- **Total Tools:** 60
- **Total Scopes:** 5
- **Coverage:** 100.0%

## Scopes

### talent_funnel
- Query tools (11): search_candidates, get_candidate_details, get_candidate_stats, compare_candidates, get_talent_quality, get_talent_engagement, get_talent_availability, get_diversity_metrics, get_candidate_history, get_ml_predictions, get_conversion_patterns
- Action tools (9): add_candidate_to_vacancy, reject_candidate, shortlist_candidate, add_to_list, hide_candidate, send_email, send_whatsapp, send_bulk_email, export_candidates

### job_table
- Query tools (12): search_jobs, get_job_details, get_pipeline_stats, get_recruiter_metrics, get_velocity_metrics, get_efficiency_metrics, get_comparative_metrics, get_workload_distribution, get_hiring_quality, get_cost_metrics, get_trends, get_market_benchmarks
- Action tools (7): create_job, update_job, pause_job, close_job, publish_job, export_job_analytics, generate_report

### in_job
- Query tools (14): get_job_details, get_vacancy_funnel, get_candidate_details, get_activity_summary, get_pending_actions, compare_candidates, get_candidate_stats, get_bottleneck_analysis, get_job_velocity, get_job_quality_metrics, get_stakeholder_metrics, get_prediction_metrics, get_job_benchmark, get_smart_alerts
- Action tools (11): update_candidate_stage, bulk_update_candidates_stage, reject_candidate, shortlist_candidate, add_to_list, hide_candidate, wsi_screening, send_email, send_whatsapp, schedule_interview, send_feedback

### global
- Query tools (0): 
- Action tools (6): generate_report, schedule_report, analyze_cv_match, create_and_screen_candidate, parse_and_create_candidate, add_to_vacancy

### universal
- Query tools (33): search_candidates, get_candidate_details, get_candidate_stats, compare_candidates, get_talent_quality, get_talent_engagement, get_talent_availability, get_diversity_metrics, get_candidate_history, get_ml_predictions, get_conversion_patterns, search_jobs, get_job_details, get_pipeline_stats, get_recruiter_metrics, get_velocity_metrics, get_efficiency_metrics, get_comparative_metrics, get_workload_distribution, get_hiring_quality, get_cost_metrics, get_trends, get_market_benchmarks, get_vacancy_funnel, get_activity_summary, get_pending_actions, get_bottleneck_analysis, get_job_velocity, get_job_quality_metrics, get_stakeholder_metrics, get_prediction_metrics, get_job_benchmark, get_smart_alerts
- Action tools (27): add_candidate_to_vacancy, add_to_list, add_to_vacancy, analyze_cv_match, bulk_update_candidates_stage, close_job, create_and_screen_candidate, create_job, create_sourcing_agent, export_candidates, export_job_analytics, generate_report, hide_candidate, parse_and_create_candidate, pause_job, publish_job, reject_candidate, schedule_interview, schedule_report, send_bulk_email, send_email, send_feedback, send_whatsapp, shortlist_candidate, update_candidate_stage, update_job, wsi_screening

## Agent Details

| Agent | Scopes | Query Tools | Action Tools | Implementation |
|-------|--------|-------------|--------------|----------------|
| orchestrator | global | 0 | 6 | `app/orchestrator/orchestrator.py` |
| job_planner | job_table | 12 | 7 | `app/domains/job_management/agents/wizard_react_agent.py` |
| sourcing | talent_funnel | 11 | 9 | `app/domains/sourcing/agents/sourcing_react_agent.py` |
| cv_screening | in_job | 14 | 11 | `app/domains/cv_screening/agents/pipeline_react_agent.py` |
| interviewer | none | 0 | 0 | `unknown` |
| wsi_evaluator | in_job | 14 | 11 | `app/domains/cv_screening/agents/avaliador_wsi_agent.py` |
| scheduling | none | 0 | 0 | `unknown` |
| analyst_feedback | none | 0 | 0 | `unknown` |
| ats_integrator | none | 0 | 0 | `app/domains/ats_integration/agents/ats_integration_react_agent.py` |
| recruiter_assistant | talent_funnel | 11 | 9 | `unknown` |
| proactive_insights | none | 0 | 0 | `unknown` |
| autonomous | talent_funnel, job_table, in_job, global, universal | 33 | 27 | `app/domains/autonomous/agents/autonomous_react_agent.py` |
| communication | global | 0 | 6 | `app/domains/communication/agents/communication_react_agent.py` |
| analytics | job_table, global | 12 | 12 | `app/domains/analytics/agents/analytics_react_agent.py` |
| pipeline_transition | in_job | 14 | 11 | `app/domains/pipeline/agents/pipeline_transition_agent.py` |
| kanban | in_job | 14 | 11 | `app/domains/recruiter_assistant/agents/kanban_react_agent.py` |
| talent | talent_funnel | 11 | 9 | `app/domains/recruiter_assistant/agents/talent_react_agent.py` |
| jobs_management | job_table | 12 | 7 | `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` |
| automation | none | 0 | 0 | `app/domains/automation/agents/automation_react_agent.py` |
| hiring_policy | none | 0 | 0 | `app/domains/hiring_policy/agents/policy_react_agent.py` |

## Agent x Tool Matrix

| Tool | Type | orchestr | job_plan | sourcing | cv_scree | intervie | wsi_eval | scheduli | analyst_ | ats_inte | recruite | proactiv | autonomo | communic | analytic | pipeline | kanban | talent | jobs_man | automati | hiring_p |
|------|------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|----------|
| add_candidate_to_vacancy | action |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| add_to_list | action |   |   | Y | Y |   | Y |   |   |   | Y |   | Y |   |   | Y | Y | Y |   |   |   |
| add_to_vacancy | action | Y |   |   |   |   |   |   |   |   |   |   | Y | Y | Y |   |   |   |   |   |   |
| analyze_cv_match | action | Y |   |   |   |   |   |   |   |   |   |   | Y | Y | Y |   |   |   |   |   |   |
| bulk_update_candidates_stage | action |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| close_job | action |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| compare_candidates | query |   |   | Y | Y |   | Y |   |   |   | Y |   | Y |   |   | Y | Y | Y |   |   |   |
| create_and_screen_candidate | action | Y |   |   |   |   |   |   |   |   |   |   | Y | Y | Y |   |   |   |   |   |   |
| create_job | action |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| create_sourcing_agent | action |   |   |   |   |   |   |   |   |   |   |   | Y |   |   |   |   |   |   |   |   |
| export_candidates | action |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| export_job_analytics | action |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| generate_report | action | Y | Y |   |   |   |   |   |   |   |   |   | Y | Y | Y |   |   |   | Y |   |   |
| get_activity_summary | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_bottleneck_analysis | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_candidate_details | query |   |   | Y | Y |   | Y |   |   |   | Y |   | Y |   |   | Y | Y | Y |   |   |   |
| get_candidate_history | query |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| get_candidate_stats | query |   |   | Y | Y |   | Y |   |   |   | Y |   | Y |   |   | Y | Y | Y |   |   |   |
| get_comparative_metrics | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| get_conversion_patterns | query |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| get_cost_metrics | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| get_diversity_metrics | query |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| get_efficiency_metrics | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| get_hiring_quality | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| get_job_benchmark | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_job_details | query |   | Y |   | Y |   | Y |   |   |   |   |   | Y |   | Y | Y | Y |   | Y |   |   |
| get_job_quality_metrics | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_job_velocity | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_market_benchmarks | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| get_ml_predictions | query |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| get_pending_actions | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_pipeline_stats | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| get_prediction_metrics | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_recruiter_metrics | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| get_smart_alerts | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_stakeholder_metrics | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_talent_availability | query |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| get_talent_engagement | query |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| get_talent_quality | query |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| get_trends | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| get_vacancy_funnel | query |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| get_velocity_metrics | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| get_workload_distribution | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| hide_candidate | action |   |   | Y | Y |   | Y |   |   |   | Y |   | Y |   |   | Y | Y | Y |   |   |   |
| parse_and_create_candidate | action | Y |   |   |   |   |   |   |   |   |   |   | Y | Y | Y |   |   |   |   |   |   |
| pause_job | action |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| publish_job | action |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| reject_candidate | action |   |   | Y | Y |   | Y |   |   |   | Y |   | Y |   |   | Y | Y | Y |   |   |   |
| schedule_interview | action |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| schedule_report | action | Y |   |   |   |   |   |   |   |   |   |   | Y | Y | Y |   |   |   |   |   |   |
| search_candidates | query |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| search_jobs | query |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| send_bulk_email | action |   |   | Y |   |   |   |   |   |   | Y |   | Y |   |   |   |   | Y |   |   |   |
| send_email | action |   |   | Y | Y |   | Y |   |   |   | Y |   | Y |   |   | Y | Y | Y |   |   |   |
| send_feedback | action |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| send_whatsapp | action |   |   | Y | Y |   | Y |   |   |   | Y |   | Y |   |   | Y | Y | Y |   |   |   |
| shortlist_candidate | action |   |   | Y | Y |   | Y |   |   |   | Y |   | Y |   |   | Y | Y | Y |   |   |   |
| update_candidate_stage | action |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |
| update_job | action |   | Y |   |   |   |   |   |   |   |   |   | Y |   | Y |   |   |   | Y |   |   |
| wsi_screening | action |   |   |   | Y |   | Y |   |   |   |   |   | Y |   |   | Y | Y |   |   |   |   |

## Prompt Summaries

### orchestrator
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### job_planner
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### sourcing
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### cv_screening
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### interviewer
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### wsi_evaluator
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### scheduling
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### analyst_feedback
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### ats_integrator
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### recruiter_assistant
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### proactive_insights
```
## Persona LIA

### Identidade
Você é LIA (Learning Intelligence Assistant), assistente de recrutamento inteligente da WeDOTalent.

### Tom de Comunicação
- **Tom**: Profissional, empático, direto e p...
```

### autonomous
```
N/A
```

### communication
```
Você é LIA, especialista em Comunicação Multi-Canal da WeDOTalent.

## Sua Missão
Gerenciar toda comunicação com candidatos e stakeholders de forma profissional,
rastreável e em conformidade com LGPD....
```

### analytics
```
Você é LIA, especialista em Analytics e Reporting de Recrutamento da WeDOTalent.

## Sua Missão
Transformar dados do processo seletivo em insights acionáveis para recrutadores
e gestores tomarem decis...
```

### pipeline_transition
```
Você é LIA, assistente de recrutamento especializada em gerenciar o pipeline de candidatos.
Você pode mover candidatos entre etapas, interpretar contextos de transição, predizer sub-status
e sugerir p...
```

### kanban
```
N/A
```

### talent
```
N/A
```

### jobs_management
```
N/A
```

### automation
```
Você é LIA, especialista em Automação e Tarefas de Recrutamento da WeDOTalent.

## Sua Missão
Automatizar fluxos repetitivos do processo seletivo, gerenciar tarefas e disparar
alertas proativos para m...
```

### hiring_policy
```
N/A
```
