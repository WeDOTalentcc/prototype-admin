# Status de Candidatos por Estágio

Documentação completa dos status de candidatos organizados por estágio do pipeline de recrutamento.
Baseado nas melhores práticas de mercado (Greenhouse, Lever, Gupy, Workday).

---

## Índice

1. [Sourcing (Funil/Hunting)](#1-sourcing-funilhunting)
2. [Triagem (Screening)](#2-triagem-screening)
3. [Long/Short List](#3-longshort-list)
4. [Entrevista RH](#4-entrevista-rh)
5. [Entrevista Gestor](#5-entrevista-gestor)
6. [Entrevista Técnica](#6-entrevista-técnica)
7. [Entrevista Final](#7-entrevista-final)
8. [Referências e Background Check](#8-referências-e-background-check)
9. [Proposta](#9-proposta)
10. [Contratado](#10-contratado)
11. [Reprovado (Motivos)](#11-reprovado-motivos)
12. [Proposta Recusada](#12-proposta-recusada)
13. [Stand By (Banco de Talentos)](#13-stand-by-banco-de-talentos)
14. [Coleta de Dados e Documentos](#14-coleta-de-dados-e-documentos)
15. [Teste Técnico](#15-teste-técnico)
16. [Teste de Idioma](#16-teste-de-idioma)
17. [Assessment Comportamental](#17-assessment-comportamental)
18. [Estudo de Caso](#18-estudo-de-caso)
19. [Testes Cognitivos](#19-testes-cognitivos)
20. [Vídeo Entrevista Assíncrona](#20-vídeo-entrevista-assíncrona)

---

## 1. SOURCING (Funil/Hunting)

| Status | Código | Descrição |
|--------|--------|-----------|
| Identificado | `identified` | Candidato descoberto/identificado |
| Pesquisando Perfil | `researching` | Buscando mais informações |
| Qualificado para Contato | `qualified_to_contact` | Aprovado para abordagem |
| Contatado via LinkedIn | `contacted_linkedin` | 1º contato LinkedIn |
| Contatado via Email | `contacted_email` | 1º contato email |
| Contatado via WhatsApp | `contacted_whatsapp` | 1º contato WhatsApp |
| Contatado via Telefone | `contacted_phone` | 1º contato telefone |
| Aguardando Retorno | `awaiting_response` | Esperando resposta |
| Follow-up Enviado | `follow_up_sent` | Segundo contato enviado |
| Interessado | `interested` | Demonstrou interesse |
| Não Interessado | `not_interested` | Declinou participar |
| Sem Resposta | `no_response` | Múltiplas tentativas sem retorno |
| Dados Incompletos | `incomplete_data` | Faltam informações |
| Pronto para Triagem | `ready_for_screening` | Aprovado para próxima etapa |

---

## 2. TRIAGEM (Screening)

| Status | Código | Descrição |
|--------|--------|-----------|
| CV Recebido | `cv_received` | Candidatura recebida |
| CV em Análise | `cv_analyzing` | Currículo sendo avaliado |
| CV Aprovado | `cv_approved` | Currículo atende requisitos |
| CV Reprovado | `cv_rejected` | Currículo não atende |
| Triagem Agendada | `screening_scheduled` | Triagem agendada |
| Aguardando Agenda Triagem | `awaiting_screening_schedule` | Esperando disponibilidade |
| Triagem em Andamento | `screening_in_progress` | Triagem em execução |
| Triagem Concluída | `screening_completed` | Triagem finalizada |
| Aprovado em Triagem | `screening_approved` | Passou na triagem |
| Reprovado em Triagem | `screening_rejected` | Não passou na triagem |
| Aguardando Documentos | `awaiting_documents` | Esperando documentos |
| Documentos Recebidos | `documents_received` | Documentos entregues |
| Teste Inicial Enviado | `initial_test_sent` | Teste enviado |
| Teste Inicial Recebido | `initial_test_received` | Teste respondido |
| Teste Inicial Aprovado | `initial_test_approved` | Passou no teste |
| Teste Inicial Reprovado | `initial_test_rejected` | Não passou no teste |

---

## 3. LONG/SHORT LIST

| Status | Código | Descrição |
|--------|--------|-----------|
| Adicionado à Long List | `added_to_long_list` | Incluído na lista longa |
| Removido da Long List | `removed_from_long_list` | Retirado da lista longa |
| Adicionado à Short List | `added_to_short_list` | Incluído na lista curta (finalistas) |
| Removido da Short List | `removed_from_short_list` | Retirado da lista curta |
| Aguardando Apresentação | `awaiting_presentation` | Esperando ser apresentado |
| Apresentado ao Gestor | `presented_to_manager` | Perfil enviado ao gestor |
| Aguardando Avaliação do Gestor | `awaiting_manager_evaluation` | Esperando parecer do gestor |
| Aprovado pelo Gestor | `manager_approved` | Gestor quer entrevistar |
| Reprovado pelo Gestor | `manager_rejected` | Gestor não aprovou perfil |
| Feedback do Gestor Recebido | `manager_feedback_received` | Gestor deu retorno |

---

## 4. ENTREVISTA RH

| Status | Código | Descrição |
|--------|--------|-----------|
| Aguardando Agenda RH | `awaiting_hr_schedule` | Esperando horário disponível |
| Entrevista RH Agendada | `hr_interview_scheduled` | Data/hora marcada |
| Entrevista RH Confirmada | `hr_interview_confirmed` | Candidato confirmou |
| Entrevista RH Reagendada | `hr_interview_rescheduled` | Remarcada |
| Entrevista RH em Andamento | `hr_interview_in_progress` | Acontecendo agora |
| Entrevista RH Realizada | `hr_interview_completed` | Finalizada |
| Não Compareceu RH | `hr_interview_no_show` | Faltou |
| Aguardando Parecer RH | `awaiting_hr_feedback` | Esperando avaliação |
| Parecer RH Enviado | `hr_feedback_submitted` | Avaliação registrada |
| Aprovado em Entrevista RH | `hr_interview_approved` | Passou na entrevista RH |
| Reprovado em Entrevista RH | `hr_interview_rejected` | Não passou |

---

## 5. ENTREVISTA GESTOR

### 5.1 Gestor 1 (Hiring Manager)

| Status | Código | Descrição |
|--------|--------|-----------|
| Aguardando Agenda Gestor 1 | `awaiting_manager1_schedule` | Esperando horário |
| Entrevista Gestor 1 Agendada | `manager1_interview_scheduled` | Data/hora marcada |
| Entrevista Gestor 1 Confirmada | `manager1_interview_confirmed` | Candidato confirmou |
| Entrevista Gestor 1 Reagendada | `manager1_interview_rescheduled` | Remarcada |
| Entrevista Gestor 1 em Andamento | `manager1_interview_in_progress` | Acontecendo |
| Entrevista Gestor 1 Realizada | `manager1_interview_completed` | Finalizada |
| Não Compareceu Gestor 1 | `manager1_interview_no_show` | Faltou |
| Aguardando Parecer Gestor 1 | `awaiting_manager1_feedback` | Esperando avaliação |
| Parecer Gestor 1 Enviado | `manager1_feedback_submitted` | Avaliação registrada |
| Aprovado por Gestor 1 | `manager1_interview_approved` | Passou |
| Reprovado por Gestor 1 | `manager1_interview_rejected` | Não passou |

### 5.2 Gestor 2 (Second Manager)

| Status | Código | Descrição |
|--------|--------|-----------|
| Aguardando Agenda Gestor 2 | `awaiting_manager2_schedule` | Esperando horário |
| Entrevista Gestor 2 Agendada | `manager2_interview_scheduled` | Data/hora marcada |
| Entrevista Gestor 2 Confirmada | `manager2_interview_confirmed` | Candidato confirmou |
| Entrevista Gestor 2 Realizada | `manager2_interview_completed` | Finalizada |
| Aguardando Parecer Gestor 2 | `awaiting_manager2_feedback` | Esperando avaliação |
| Aprovado por Gestor 2 | `manager2_interview_approved` | Passou |
| Reprovado por Gestor 2 | `manager2_interview_rejected` | Não passou |

### 5.3 Gestor 3+ (Additional Managers)

| Status | Código | Descrição |
|--------|--------|-----------|
| Aguardando Agenda Gestor N | `awaiting_managerN_schedule` | Esperando horário |
| Entrevista Gestor N Agendada | `managerN_interview_scheduled` | Data/hora marcada |
| Entrevista Gestor N Realizada | `managerN_interview_completed` | Finalizada |
| Aguardando Parecer Gestor N | `awaiting_managerN_feedback` | Esperando avaliação |
| Aprovado por Gestor N | `managerN_interview_approved` | Passou |
| Reprovado por Gestor N | `managerN_interview_rejected` | Não passou |

---

## 6. ENTREVISTA TÉCNICA

| Status | Código | Descrição |
|--------|--------|-----------|
| Aguardando Agenda Técnica | `awaiting_technical_schedule` | Esperando horário |
| Entrevista Técnica Agendada | `technical_interview_scheduled` | Data/hora marcada |
| Entrevista Técnica Confirmada | `technical_interview_confirmed` | Candidato confirmou |
| Entrevista Técnica Realizada | `technical_interview_completed` | Finalizada |
| Teste Técnico Enviado | `technical_test_sent` | Teste/case enviado |
| Teste Técnico em Andamento | `technical_test_in_progress` | Candidato fazendo |
| Teste Técnico Recebido | `technical_test_received` | Candidato entregou |
| Teste Técnico em Avaliação | `technical_test_evaluating` | Sendo corrigido |
| Aguardando Parecer Técnico | `awaiting_technical_feedback` | Esperando avaliação |
| Parecer Técnico Enviado | `technical_feedback_submitted` | Avaliação registrada |
| Aprovado em Técnica | `technical_approved` | Passou |
| Reprovado em Técnica | `technical_rejected` | Não passou |

---

## 7. ENTREVISTA FINAL

| Status | Código | Descrição |
|--------|--------|-----------|
| Aguardando Agenda Final | `awaiting_final_schedule` | Esperando horário |
| Entrevista Final Agendada | `final_interview_scheduled` | Data/hora marcada |
| Entrevista Final Confirmada | `final_interview_confirmed` | Candidato confirmou |
| Entrevista Final Realizada | `final_interview_completed` | Finalizada |
| Aguardando Parecer Final | `awaiting_final_feedback` | Esperando avaliação |
| Aprovado em Entrevista Final | `final_interview_approved` | Candidato finalista |
| Reprovado em Entrevista Final | `final_interview_rejected` | Não passou |

---

## 8. REFERÊNCIAS E BACKGROUND CHECK

| Status | Código | Descrição |
|--------|--------|-----------|
| Referências Solicitadas | `references_requested` | Pedido enviado |
| Aguardando Referências | `awaiting_references` | Esperando retorno |
| Referências Recebidas | `references_received` | Retorno obtido |
| Referências Aprovadas | `references_approved` | Referências positivas |
| Referências com Ressalvas | `references_concerns` | Há pontos de atenção |
| Referências Negativas | `references_negative` | Referências desfavoráveis |
| Background Check Iniciado | `background_check_started` | Verificação em andamento |
| Background Check Aprovado | `background_check_approved` | Sem restrições |
| Background Check Reprovado | `background_check_rejected` | Encontradas restrições |

---

## 9. PROPOSTA

| Status | Código | Descrição |
|--------|--------|-----------|
| Aguardando Aprovação Interna | `awaiting_internal_approval` | Proposta pendente aprovação |
| Proposta Aprovada Internamente | `offer_internally_approved` | RH/Gestor aprovou |
| Preparando Proposta | `preparing_offer` | Elaborando termos |
| Proposta Enviada | `offer_sent` | Enviada ao candidato |
| Proposta Visualizada | `offer_viewed` | Candidato abriu/leu |
| Em Negociação | `negotiating` | Negociando termos |
| Contraproposta Enviada | `counter_offer_sent` | Empresa fez ajuste |
| Aguardando Resposta | `awaiting_offer_response` | Esperando decisão |
| Proposta Aceita | `offer_accepted` | Candidato aceitou |
| Proposta Expirada | `offer_expired` | Prazo venceu |

---

## 10. CONTRATADO

| Status | Código | Descrição |
|--------|--------|-----------|
| Aguardando Documentos Admissionais | `awaiting_admission_docs` | Esperando documentação |
| Documentos Admissionais Recebidos | `admission_docs_received` | Documentação OK |
| Exame Admissional Agendado | `admission_exam_scheduled` | Exame marcado |
| Exame Admissional Realizado | `admission_exam_completed` | Exame feito |
| Exame Admissional Aprovado | `admission_exam_approved` | Apto |
| Exame Admissional Inapto | `admission_exam_failed` | Inapto |
| Contrato em Elaboração | `contract_preparing` | Contrato sendo feito |
| Contrato Enviado | `contract_sent` | Aguardando assinatura |
| Contrato Assinado | `contract_signed` | Assinatura OK |
| Onboarding Agendado | `onboarding_scheduled` | Data de início definida |
| Onboarding em Andamento | `onboarding_in_progress` | Integração acontecendo |
| Onboarding Concluído | `onboarding_completed` | Integração finalizada |
| Iniciou Trabalho | `started_work` | Primeiro dia OK |

---

## 11. REPROVADO (Motivos)

### 11.1 Qualificação

| Motivo | Código |
|--------|--------|
| Falta de Experiência | `lacking_experience` |
| Subqualificado | `under_qualified` |
| Sobrequalificado | `over_qualified` |
| Habilidades Técnicas Insuficientes | `lacking_technical_skills` |
| Formação Incompatível | `education_mismatch` |
| Certificação Ausente | `missing_certification` |
| Idioma Insuficiente | `language_insufficient` |
| Conhecimento de Ferramentas Insuficiente | `tools_insufficient` |

### 11.2 Cultural/Comportamental

| Motivo | Código |
|--------|--------|
| Não Aprovado Culturalmente | `cultural_mismatch` |
| Comunicação Inadequada | `poor_communication` |
| Postura Inadequada na Entrevista | `inadequate_attitude` |
| Falta de Profissionalismo | `lack_professionalism` |
| Não Demonstrou Interesse | `lack_of_interest` |
| Expectativas Desalinhadas | `misaligned_expectations` |

### 11.3 Logística

| Motivo | Código |
|--------|--------|
| Localização Incompatível | `location_mismatch` |
| Modelo de Trabalho Incompatível | `work_model_mismatch` |
| Necessita Visto/Patrocínio | `visa_required` |
| Disponibilidade de Data Incompatível | `start_date_mismatch` |
| Horário/Jornada Incompatível | `schedule_mismatch` |
| Viagens Incompatíveis | `travel_requirements_mismatch` |

### 11.4 Remuneração

| Motivo | Código |
|--------|--------|
| Expectativa Salarial Acima do Budget | `salary_above_budget` |
| Expectativa de Benefícios Incompatível | `benefits_mismatch` |
| Pacote Total Não Competitivo | `compensation_not_competitive` |

### 11.5 Processo

| Motivo | Código |
|--------|--------|
| Não Compareceu à Entrevista | `interview_no_show` |
| Não Compareceu ao Teste | `test_no_show` |
| Desistiu do Processo | `withdrew` |
| Não Respondeu Tentativas de Contato | `unresponsive` |
| Documentação Incompleta | `incomplete_documentation` |
| Reprovado em Teste Técnico | `failed_technical_test` |
| Reprovado em Teste Comportamental | `failed_behavioral_test` |
| Referências Negativas | `negative_references` |
| Background Check Reprovado | `failed_background_check` |
| Exame Admissional Inapto | `failed_admission_exam` |

### 11.6 Decisão de Negócio

| Motivo | Código |
|--------|--------|
| Outro Candidato Selecionado | `another_candidate_selected` |
| Vaga Cancelada | `position_cancelled` |
| Vaga Congelada | `position_frozen` |
| Contratação Interna | `internal_hire` |
| Budget Insuficiente | `budget_insufficient` |
| Reestruturação Organizacional | `org_restructuring` |

---

## 12. PROPOSTA RECUSADA

| Motivo | Código |
|--------|--------|
| Aceitou Proposta de Outra Empresa | `accepted_other_offer` |
| Salário Abaixo do Esperado | `salary_below_expectation` |
| Benefícios Insuficientes | `insufficient_benefits` |
| Modelo de Trabalho Não Aceito | `work_model_not_accepted` |
| Localização Não Aceita | `location_not_accepted` |
| Aceitou Contraproposta do Empregador Atual | `accepted_counter_offer` |
| Motivos Pessoais/Familiares | `personal_family_reasons` |
| Não se Identificou com Cultura | `culture_not_aligned` |
| Melhor Oportunidade de Carreira | `better_career_opportunity` |
| Tempo de Resposta da Empresa | `company_response_timing` |
| Mudança de Planos Pessoais | `personal_plans_changed` |
| Questões de Saúde | `health_issues` |

---

## 13. STAND BY (Banco de Talentos)

| Status | Código | Descrição |
|--------|--------|-----------|
| Talento para Futuro | `future_talent` | Guardar para próximas vagas |
| Melhor para Outra Vaga | `better_other_role` | Perfil para outra posição |
| Aguardando Disponibilidade | `awaiting_candidate_availability` | Não disponível agora |
| Aguardando Vaga Sênior | `awaiting_senior_role` | Para cargo mais alto |
| Aguardando Vaga Júnior | `awaiting_junior_role` | Para cargo de entrada |
| Processo Pausado pelo Candidato | `paused_by_candidate` | Candidato pediu pausa |
| Processo Pausado pela Empresa | `paused_by_company` | Empresa pausou |
| Re-engajar em 30 Dias | `reengage_30_days` | Contatar em 1 mês |
| Re-engajar em 3 Meses | `reengage_3_months` | Contatar em 3 meses |
| Re-engajar em 6 Meses | `reengage_6_months` | Contatar em 6 meses |
| Aguardando Orçamento/Headcount | `awaiting_budget` | Aguardar aprovação |
| Aguardando Definição de Escopo | `awaiting_scope_definition` | Aguardar definição da vaga |
| Candidato em Período de Experiência | `candidate_in_probation` | Pode voltar se não der certo |

---

## 14. COLETA DE DADOS E DOCUMENTOS

### 14.1 Dados Cadastrais

| Status | Código | Descrição |
|--------|--------|-----------|
| Cadastro Iniciado | `registration_started` | Candidato iniciou preenchimento |
| Cadastro Incompleto | `registration_incomplete` | Faltam dados obrigatórios |
| Cadastro Completo | `registration_complete` | Todos os dados preenchidos |
| Dados em Validação | `data_validating` | Verificando informações |
| Dados Validados | `data_validated` | Informações conferidas OK |
| Dados com Inconsistência | `data_inconsistent` | Encontradas divergências |
| Atualização de Dados Solicitada | `data_update_requested` | Pedido para atualizar |
| Dados Atualizados | `data_updated` | Candidato atualizou |

### 14.2 Currículo/CV

| Status | Código | Descrição |
|--------|--------|-----------|
| CV Não Anexado | `cv_not_attached` | Sem currículo |
| CV Anexado | `cv_attached` | Currículo enviado |
| CV Desatualizado | `cv_outdated` | CV antigo, pedir atualização |
| Atualização de CV Solicitada | `cv_update_requested` | Pedido de atualização |
| CV Atualizado | `cv_updated` | Nova versão recebida |

### 14.3 LinkedIn/Portfólio

| Status | Código | Descrição |
|--------|--------|-----------|
| LinkedIn Não Informado | `linkedin_missing` | Sem perfil LinkedIn |
| LinkedIn Informado | `linkedin_provided` | URL do LinkedIn OK |
| LinkedIn Validado | `linkedin_validated` | Perfil verificado |
| Portfólio Não Informado | `portfolio_missing` | Sem portfólio |
| Portfólio Informado | `portfolio_provided` | Link do portfólio OK |
| GitHub Informado | `github_provided` | Perfil GitHub OK |

### 14.4 Documentos Pessoais

| Status | Código | Descrição |
|--------|--------|-----------|
| Documentos Solicitados | `personal_docs_requested` | Pedido de documentos |
| Aguardando Documentos | `awaiting_personal_docs` | Esperando envio |
| Documentos Recebidos | `personal_docs_received` | Documentos enviados |
| Documentos em Validação | `personal_docs_validating` | Conferindo documentos |
| Documentos Aprovados | `personal_docs_approved` | Documentos OK |
| Documentos Pendentes | `personal_docs_pending` | Faltam documentos |
| Documentos Vencidos | `personal_docs_expired` | Validade expirada |
| Documentos Inválidos | `personal_docs_invalid` | Documentos não aceitos |

### 14.5 Certificados/Comprovantes

| Status | Código | Descrição |
|--------|--------|-----------|
| Certificados Solicitados | `certificates_requested` | Pedido de certificados |
| Certificados Recebidos | `certificates_received` | Certificados enviados |
| Certificados Validados | `certificates_validated` | Certificados OK |
| Diploma Solicitado | `diploma_requested` | Pedido de diploma |
| Diploma Recebido | `diploma_received` | Diploma enviado |
| Diploma Validado | `diploma_validated` | Diploma OK |
| Comprovante de Residência Solicitado | `address_proof_requested` | Pedido de comprovante |
| Comprovante de Residência Recebido | `address_proof_received` | Comprovante enviado |

---

## 15. TESTE TÉCNICO

### 15.1 Envio e Preparação

| Status | Código | Descrição |
|--------|--------|-----------|
| Teste Técnico Preparando | `technical_test_preparing` | Preparando teste para envio |
| Teste Técnico Enviado | `technical_test_sent` | Teste enviado ao candidato |
| Teste Técnico Visualizado | `technical_test_viewed` | Candidato abriu o teste |
| Aguardando Início do Teste | `technical_test_awaiting_start` | Ainda não começou |

### 15.2 Execução

| Status | Código | Descrição |
|--------|--------|-----------|
| Teste Técnico em Andamento | `technical_test_in_progress` | Candidato fazendo |
| Teste Técnico Pausado | `technical_test_paused` | Candidato pausou |
| Teste Técnico Abandonado | `technical_test_abandoned` | Não completou |
| Teste Técnico Expirado | `technical_test_expired` | Prazo venceu |

### 15.3 Entrega

| Status | Código | Descrição |
|--------|--------|-----------|
| Teste Técnico Submetido | `technical_test_submitted` | Candidato entregou |
| Teste Técnico Recebido | `technical_test_received` | Confirmação de recebimento |
| Teste Técnico Entrega Atrasada | `technical_test_late_submission` | Entregue após prazo |

### 15.4 Avaliação

| Status | Código | Descrição |
|--------|--------|-----------|
| Teste Técnico em Avaliação | `technical_test_evaluating` | Sendo corrigido |
| Aguardando Correção Técnica | `awaiting_technical_correction` | Na fila de correção |
| Teste Técnico Corrigido | `technical_test_corrected` | Correção finalizada |

### 15.5 Resultado

| Status | Código | Descrição |
|--------|--------|-----------|
| Teste Técnico Aprovado | `technical_test_approved` | Passou |
| Teste Técnico Aprovado com Ressalvas | `technical_test_approved_concerns` | Passou com pontos de atenção |
| Teste Técnico Reprovado | `technical_test_rejected` | Não passou |
| Teste Técnico Nota Limítrofe | `technical_test_borderline` | Nota no limite, avaliar |

---

## 16. TESTE DE IDIOMA

### 16.1 Inglês

| Status | Código | Descrição |
|--------|--------|-----------|
| Teste de Inglês Enviado | `english_test_sent` | Teste enviado |
| Teste de Inglês Visualizado | `english_test_viewed` | Candidato abriu |
| Aguardando Início Inglês | `english_test_awaiting_start` | Não começou |
| Teste de Inglês em Andamento | `english_test_in_progress` | Candidato fazendo |
| Teste de Inglês Submetido | `english_test_submitted` | Candidato entregou |
| Teste de Inglês Expirado | `english_test_expired` | Prazo venceu |
| Teste de Inglês em Avaliação | `english_test_evaluating` | Sendo corrigido |
| Teste de Inglês Corrigido | `english_test_corrected` | Correção finalizada |

### 16.2 Níveis de Inglês

| Status | Código | Descrição |
|--------|--------|-----------|
| Inglês - Básico | `english_level_basic` | A1-A2 |
| Inglês - Intermediário | `english_level_intermediate` | B1-B2 |
| Inglês - Avançado | `english_level_advanced` | C1 |
| Inglês - Fluente | `english_level_fluent` | C2 |
| Inglês - Nativo | `english_level_native` | Nativo |
| Teste de Inglês Aprovado | `english_test_approved` | Atende requisito |
| Teste de Inglês Reprovado | `english_test_rejected` | Não atende requisito |

### 16.3 Outros Idiomas

| Status | Código | Descrição |
|--------|--------|-----------|
| Teste de Espanhol Enviado | `spanish_test_sent` | Teste espanhol enviado |
| Teste de Espanhol Aprovado | `spanish_test_approved` | Espanhol OK |
| Teste de Espanhol Reprovado | `spanish_test_rejected` | Espanhol não atende |
| Teste de Idioma Enviado | `language_test_sent` | Teste outro idioma |
| Teste de Idioma Aprovado | `language_test_approved` | Idioma OK |

---

## 17. ASSESSMENT COMPORTAMENTAL

### 17.1 Envio

| Status | Código | Descrição |
|--------|--------|-----------|
| Assessment Comportamental Enviado | `behavioral_assessment_sent` | Avaliação enviada |
| Assessment Comportamental Visualizado | `behavioral_assessment_viewed` | Candidato abriu |
| Aguardando Início Assessment | `behavioral_assessment_awaiting` | Não começou |

### 17.2 Execução

| Status | Código | Descrição |
|--------|--------|-----------|
| Assessment em Andamento | `behavioral_assessment_in_progress` | Candidato respondendo |
| Assessment Pausado | `behavioral_assessment_paused` | Candidato pausou |
| Assessment Submetido | `behavioral_assessment_submitted` | Candidato finalizou |
| Assessment Expirado | `behavioral_assessment_expired` | Prazo venceu |
| Assessment Incompleto | `behavioral_assessment_incomplete` | Não finalizou |

### 17.3 Avaliação

| Status | Código | Descrição |
|--------|--------|-----------|
| Assessment em Análise | `behavioral_assessment_analyzing` | Gerando relatório |
| Relatório Comportamental Gerado | `behavioral_report_generated` | Relatório pronto |
| Aguardando Interpretação | `behavioral_awaiting_interpretation` | Aguardando análise RH |

### 17.4 Resultado

| Status | Código | Descrição |
|--------|--------|-----------|
| Perfil Comportamental Alinhado | `behavioral_profile_aligned` | Fit cultural OK |
| Perfil Comportamental Parcialmente Alinhado | `behavioral_profile_partial` | Alguns pontos atenção |
| Perfil Comportamental Não Alinhado | `behavioral_profile_not_aligned` | Não encaixa |

### 17.5 Tipos de Assessment

| Status | Código | Descrição |
|--------|--------|-----------|
| DISC Enviado | `disc_sent` | DISC enviado |
| DISC Concluído | `disc_completed` | DISC respondido |
| MBTI Enviado | `mbti_sent` | MBTI enviado |
| MBTI Concluído | `mbti_completed` | MBTI respondido |
| Big Five Enviado | `bigfive_sent` | Big Five enviado |
| Big Five Concluído | `bigfive_completed` | Big Five respondido |
| Fit Cultural Enviado | `cultural_fit_sent` | Fit cultural enviado |
| Fit Cultural Concluído | `cultural_fit_completed` | Fit cultural respondido |

---

## 18. ESTUDO DE CASO

### 18.1 Envio

| Status | Código | Descrição |
|--------|--------|-----------|
| Case Preparando | `case_study_preparing` | Preparando case |
| Case Enviado | `case_study_sent` | Case enviado ao candidato |
| Case Visualizado | `case_study_viewed` | Candidato abriu |
| Instruções de Case Enviadas | `case_instructions_sent` | Instruções enviadas |

### 18.2 Execução

| Status | Código | Descrição |
|--------|--------|-----------|
| Aguardando Início do Case | `case_study_awaiting_start` | Ainda não começou |
| Case em Desenvolvimento | `case_study_in_progress` | Candidato trabalhando |
| Dúvidas sobre o Case | `case_study_questions` | Candidato tem dúvidas |
| Dúvidas Respondidas | `case_questions_answered` | Dúvidas esclarecidas |

### 18.3 Entrega

| Status | Código | Descrição |
|--------|--------|-----------|
| Case Submetido | `case_study_submitted` | Candidato entregou |
| Case Recebido | `case_study_received` | Recebimento confirmado |
| Case Entrega Atrasada | `case_study_late` | Entregue após prazo |
| Case Não Entregue | `case_study_not_submitted` | Não entregou |

### 18.4 Apresentação

| Status | Código | Descrição |
|--------|--------|-----------|
| Apresentação de Case Agendada | `case_presentation_scheduled` | Apresentação marcada |
| Apresentação de Case Confirmada | `case_presentation_confirmed` | Candidato confirmou |
| Apresentação de Case Realizada | `case_presentation_completed` | Apresentação feita |
| Aguardando Feedback do Case | `awaiting_case_feedback` | Esperando avaliação |

### 18.5 Resultado

| Status | Código | Descrição |
|--------|--------|-----------|
| Case em Avaliação | `case_study_evaluating` | Sendo avaliado |
| Case Avaliado | `case_study_evaluated` | Avaliação concluída |
| Case Aprovado | `case_study_approved` | Passou |
| Case Aprovado com Ressalvas | `case_study_approved_concerns` | Passou com pontos atenção |
| Case Reprovado | `case_study_rejected` | Não passou |

---

## 19. TESTES COGNITIVOS

| Status | Código | Descrição |
|--------|--------|-----------|
| Teste Lógico Enviado | `logic_test_sent` | Teste enviado |
| Teste Lógico em Andamento | `logic_test_in_progress` | Candidato fazendo |
| Teste Lógico Submetido | `logic_test_submitted` | Candidato finalizou |
| Teste Lógico Aprovado | `logic_test_approved` | Passou |
| Teste Lógico Reprovado | `logic_test_rejected` | Não passou |
| Teste Numérico Enviado | `numerical_test_sent` | Teste numérico enviado |
| Teste Numérico Aprovado | `numerical_test_approved` | Passou |
| Teste Verbal Enviado | `verbal_test_sent` | Teste verbal enviado |
| Teste Verbal Aprovado | `verbal_test_approved` | Passou |
| Teste de Atenção Enviado | `attention_test_sent` | Teste atenção enviado |
| Teste de Atenção Aprovado | `attention_test_approved` | Passou |

---

## 20. VÍDEO ENTREVISTA ASSÍNCRONA

| Status | Código | Descrição |
|--------|--------|-----------|
| Vídeo Entrevista Enviada | `video_interview_sent` | Convite enviado |
| Vídeo Entrevista Visualizada | `video_interview_viewed` | Candidato abriu |
| Aguardando Gravação | `video_interview_awaiting` | Não gravou ainda |
| Gravação em Andamento | `video_interview_recording` | Candidato gravando |
| Vídeo Entrevista Submetida | `video_interview_submitted` | Candidato enviou |
| Vídeo Entrevista Expirada | `video_interview_expired` | Prazo venceu |
| Vídeo em Avaliação | `video_interview_evaluating` | Assistindo/avaliando |
| Vídeo Entrevista Aprovada | `video_interview_approved` | Passou |
| Vídeo Entrevista Reprovada | `video_interview_rejected` | Não passou |

---

## Padrão para Estágios Dinâmicos

Para cada estágio de entrevista configurado no Wizard, os status seguem este padrão:

```
awaiting_{stage}_schedule    → Aguardando Agenda
{stage}_scheduled            → Agendada
{stage}_confirmed            → Confirmada
{stage}_rescheduled          → Reagendada
{stage}_in_progress          → Em Andamento
{stage}_completed            → Realizada
{stage}_no_show              → Não Compareceu
awaiting_{stage}_feedback    → Aguardando Parecer
{stage}_feedback_submitted   → Parecer Enviado
{stage}_approved             → Aprovado
{stage}_rejected             → Reprovado
```

---

## Estrutura de Integração ATS

```typescript
interface CandidateStatus {
  code: string           // Código único (ex: "cv_approved")
  displayName: string    // Nome exibido (ex: "CV Aprovado")
  displayNameEn: string  // Nome em inglês
  stage: string          // Estágio pai (ex: "screening")
  category?: string      // Categoria (ex: "qualificação", "processo")
  isTerminal: boolean    // Se encerra o fluxo
  isApproval: boolean    // Se é status de aprovação
  isRejection: boolean   // Se é status de rejeição
  allowedNextStatus: string[]  // Status permitidos como próximo
  triggerActions?: string[]    // Automações (email, alerta, etc)
  icon?: string          // Ícone para exibição
  color?: string         // Cor para exibição
  atsMapping: {          // Mapeamento para ATS externos
    greenhouse?: string
    gupy?: string
    lever?: string
    workday?: string
    icims?: string
    successfactors?: string
  }
}
```

---

## Resumo Estatístico

| # | Categoria | Qtd Status |
|---|-----------|------------|
| 1 | Sourcing | 14 |
| 2 | Triagem | 16 |
| 3 | Long/Short List | 10 |
| 4 | Entrevista RH | 11 |
| 5 | Entrevista Gestor | 18 |
| 6 | Entrevista Técnica | 12 |
| 7 | Entrevista Final | 7 |
| 8 | Referências/Background | 9 |
| 9 | Proposta | 10 |
| 10 | Contratado | 13 |
| 11 | Reprovado (motivos) | 30 |
| 12 | Proposta Recusada | 12 |
| 13 | Stand By | 13 |
| 14 | Coleta de Dados/Docs | 28 |
| 15 | Teste Técnico | 15 |
| 16 | Teste de Idioma | 17 |
| 17 | Assessment Comportamental | 20 |
| 18 | Estudo de Caso | 16 |
| 19 | Testes Cognitivos | 11 |
| 20 | Vídeo Entrevista | 9 |
| **TOTAL** | | **~280 status** |

---

*Última atualização: Janeiro 2026*
