import type { StatusCategory } from './stages-data'

export interface SubStatus {
  name: string
  displayName: string
  displayNameEn?: string
  isDefault?: boolean
  isWaiting?: boolean
  isApproval?: boolean
  isRejection?: boolean
  waitingFor?: 'candidate' | 'interviewer' | 'manager' | 'hr' | 'system'
  category?: StatusCategory
  icon?: string
  color?: string
}

export interface CandidateSource {
  id: string
  name: string
  displayName: string
  icon: string
  color: string
}

export interface RejectionReason {
  code: string
  displayName: string
  displayNameEn: string
  category: StatusCategory
}

export interface OfferDeclineReason {
  code: string
  displayName: string
  displayNameEn: string
}

export interface StandbyReason {
  code: string
  displayName: string
  displayNameEn: string
}
export const SUB_STATUSES: Record<string, SubStatus[]> = {
  // SOURCING
  sourcing: [
    { name: 'identified', displayName: 'Identificado', displayNameEn: 'Identified', isDefault: true },
    { name: 'researching', displayName: 'Pesquisando Perfil', displayNameEn: 'Researching Profile' },
    { name: 'qualified_to_contact', displayName: 'Qualificado para Contato', displayNameEn: 'Qualified to Contact' },
    { name: 'contacted_linkedin', displayName: 'Contatado via LinkedIn', displayNameEn: 'Contacted via LinkedIn' },
    { name: 'contacted_email', displayName: 'Contatado via Email', displayNameEn: 'Contacted via Email' },
    { name: 'contacted_whatsapp', displayName: 'Contatado via WhatsApp', displayNameEn: 'Contacted via WhatsApp' },
    { name: 'contacted_phone', displayName: 'Contatado via Telefone', displayNameEn: 'Contacted via Phone' },
    { name: 'awaiting_response', displayName: 'Aguardando Retorno', displayNameEn: 'Awaiting Response', isWaiting: true, waitingFor: 'candidate' },
    { name: 'follow_up_sent', displayName: 'Follow-up Enviado', displayNameEn: 'Follow-up Sent' },
    { name: 'interested', displayName: 'Interessado', displayNameEn: 'Interested' },
    { name: 'not_interested', displayName: 'Não Interessado', displayNameEn: 'Not Interested' },
    { name: 'no_response', displayName: 'Sem Resposta', displayNameEn: 'No Response' },
    { name: 'incomplete_data', displayName: 'Dados Incompletos', displayNameEn: 'Incomplete Data' },
    { name: 'ready_for_screening', displayName: 'Pronto para Triagem', displayNameEn: 'Ready for Screening', isApproval: true },
  ],
  
  // SCREENING
  screening: [
    { name: 'cv_received', displayName: 'CV Recebido', displayNameEn: 'CV Received', isDefault: true },
    { name: 'cv_analyzing', displayName: 'CV em Análise', displayNameEn: 'CV Analyzing' },
    { name: 'cv_approved', displayName: 'CV Aprovado', displayNameEn: 'CV Approved', isApproval: true },
    { name: 'cv_rejected', displayName: 'CV Reprovado', displayNameEn: 'CV Rejected', isRejection: true },
    { name: 'awaiting_screening_schedule', displayName: 'Aguardando Agenda Triagem', displayNameEn: 'Awaiting Screening Schedule', isWaiting: true, waitingFor: 'candidate' },
    { name: 'screening_scheduled', displayName: 'Triagem Agendada', displayNameEn: 'Screening Scheduled' },
    { name: 'screening_in_progress', displayName: 'Triagem em Andamento', displayNameEn: 'Screening in Progress' },
    { name: 'screening_completed', displayName: 'Triagem Concluída', displayNameEn: 'Screening Completed' },
    { name: 'screening_approved', displayName: 'Aprovado em Triagem', displayNameEn: 'Screening Approved', isApproval: true },
    { name: 'screening_rejected', displayName: 'Reprovado em Triagem', displayNameEn: 'Screening Rejected', isRejection: true },
    { name: 'awaiting_documents', displayName: 'Aguardando Documentos', displayNameEn: 'Awaiting Documents', isWaiting: true, waitingFor: 'candidate' },
    { name: 'documents_received', displayName: 'Documentos Recebidos', displayNameEn: 'Documents Received' },
    { name: 'initial_test_sent', displayName: 'Teste Inicial Enviado', displayNameEn: 'Initial Test Sent' },
    { name: 'initial_test_received', displayName: 'Teste Inicial Recebido', displayNameEn: 'Initial Test Received' },
    { name: 'initial_test_approved', displayName: 'Teste Inicial Aprovado', displayNameEn: 'Initial Test Approved', isApproval: true },
    { name: 'initial_test_rejected', displayName: 'Teste Inicial Reprovado', displayNameEn: 'Initial Test Rejected', isRejection: true },
  ],
  
  // LONG LIST
  long_list: [
    { name: 'added_to_long_list', displayName: 'Adicionado à Long List', displayNameEn: 'Added to Long List', isDefault: true },
    { name: 'removed_from_long_list', displayName: 'Removido da Long List', displayNameEn: 'Removed from Long List' },
    { name: 'awaiting_presentation', displayName: 'Aguardando Apresentação', displayNameEn: 'Awaiting Presentation', isWaiting: true, waitingFor: 'hr' },
    { name: 'presented_to_manager', displayName: 'Apresentado ao Gestor', displayNameEn: 'Presented to Manager' },
    { name: 'awaiting_manager_evaluation', displayName: 'Aguardando Avaliação do Gestor', displayNameEn: 'Awaiting Manager Evaluation', isWaiting: true, waitingFor: 'manager' },
    { name: 'manager_approved', displayName: 'Aprovado pelo Gestor', displayNameEn: 'Manager Approved', isApproval: true },
    { name: 'manager_rejected', displayName: 'Reprovado pelo Gestor', displayNameEn: 'Manager Rejected', isRejection: true },
    { name: 'manager_feedback_received', displayName: 'Feedback do Gestor Recebido', displayNameEn: 'Manager Feedback Received' },
  ],
  
  // SHORT LIST
  short_list: [
    { name: 'added_to_short_list', displayName: 'Adicionado à Short List', displayNameEn: 'Added to Short List', isDefault: true },
    { name: 'removed_from_short_list', displayName: 'Removido da Short List', displayNameEn: 'Removed from Short List' },
    { name: 'awaiting_presentation', displayName: 'Aguardando Apresentação', displayNameEn: 'Awaiting Presentation', isWaiting: true, waitingFor: 'hr' },
    { name: 'presented_to_manager', displayName: 'Apresentado ao Gestor', displayNameEn: 'Presented to Manager' },
    { name: 'awaiting_manager_evaluation', displayName: 'Aguardando Avaliação do Gestor', displayNameEn: 'Awaiting Manager Evaluation', isWaiting: true, waitingFor: 'manager' },
    { name: 'manager_approved', displayName: 'Aprovado pelo Gestor', displayNameEn: 'Manager Approved', isApproval: true },
    { name: 'manager_rejected', displayName: 'Reprovado pelo Gestor', displayNameEn: 'Manager Rejected', isRejection: true },
  ],
  
  // INTERVIEW HR
  interview_hr: [
    { name: 'awaiting_hr_schedule', displayName: 'Aguardando Agenda RH', displayNameEn: 'Awaiting HR Schedule', isWaiting: true, waitingFor: 'hr' },
    { name: 'hr_interview_scheduled', displayName: 'Entrevista RH Agendada', displayNameEn: 'HR Interview Scheduled', isDefault: true },
    { name: 'hr_interview_confirmed', displayName: 'Entrevista RH Confirmada', displayNameEn: 'HR Interview Confirmed' },
    { name: 'hr_interview_rescheduled', displayName: 'Entrevista RH Reagendada', displayNameEn: 'HR Interview Rescheduled' },
    { name: 'hr_interview_in_progress', displayName: 'Entrevista RH em Andamento', displayNameEn: 'HR Interview in Progress' },
    { name: 'hr_interview_completed', displayName: 'Entrevista RH Realizada', displayNameEn: 'HR Interview Completed' },
    { name: 'hr_interview_no_show', displayName: 'Não Compareceu RH', displayNameEn: 'HR Interview No Show' },
    { name: 'awaiting_hr_feedback', displayName: 'Aguardando Parecer RH', displayNameEn: 'Awaiting HR Feedback', isWaiting: true, waitingFor: 'interviewer' },
    { name: 'hr_feedback_submitted', displayName: 'Parecer RH Enviado', displayNameEn: 'HR Feedback Submitted' },
    { name: 'hr_interview_approved', displayName: 'Aprovado em Entrevista RH', displayNameEn: 'HR Interview Approved', isApproval: true },
    { name: 'hr_interview_rejected', displayName: 'Reprovado em Entrevista RH', displayNameEn: 'HR Interview Rejected', isRejection: true },
  ],
  
  // TECHNICAL TEST
  technical_test: [
    { name: 'test_pending', displayName: 'Teste Pendente', displayNameEn: 'Test Pending', isDefault: true },
    { name: 'test_link_sent', displayName: 'Link do Teste Enviado', displayNameEn: 'Test Link Sent' },
    { name: 'test_in_progress', displayName: 'Teste em Andamento', displayNameEn: 'Test in Progress' },
    { name: 'test_submitted', displayName: 'Teste Submetido', displayNameEn: 'Test Submitted' },
    { name: 'awaiting_evaluation', displayName: 'Aguardando Avaliação', displayNameEn: 'Awaiting Evaluation', isWaiting: true, waitingFor: 'hr' },
    { name: 'test_evaluating', displayName: 'Teste em Avaliação', displayNameEn: 'Test Evaluating' },
    { name: 'test_approved', displayName: 'Aprovado no Teste', displayNameEn: 'Test Approved', isApproval: true },
    { name: 'test_conditional', displayName: 'Aprovado com Ressalvas', displayNameEn: 'Test Conditional' },
    { name: 'test_rejected', displayName: 'Reprovado no Teste', displayNameEn: 'Test Rejected', isRejection: true },
    { name: 'test_expired', displayName: 'Teste Expirado', displayNameEn: 'Test Expired' },
    { name: 'test_no_show', displayName: 'Não Realizou o Teste', displayNameEn: 'Test No Show' },
  ],
  
  // ENGLISH TEST
  english_test: [
    { name: 'english_test_pending', displayName: 'Teste de Inglês Pendente', displayNameEn: 'English Test Pending', isDefault: true },
    { name: 'english_test_link_sent', displayName: 'Link do Teste Enviado', displayNameEn: 'Test Link Sent' },
    { name: 'english_test_in_progress', displayName: 'Teste em Andamento', displayNameEn: 'Test in Progress' },
    { name: 'english_test_submitted', displayName: 'Teste Submetido', displayNameEn: 'Test Submitted' },
    { name: 'awaiting_english_evaluation', displayName: 'Aguardando Avaliação', displayNameEn: 'Awaiting Evaluation', isWaiting: true, waitingFor: 'hr' },
    { name: 'english_test_evaluating', displayName: 'Teste em Avaliação', displayNameEn: 'Test Evaluating' },
    { name: 'english_level_advanced', displayName: 'Nível Avançado', displayNameEn: 'Advanced Level', isApproval: true },
    { name: 'english_level_intermediate', displayName: 'Nível Intermediário', displayNameEn: 'Intermediate Level' },
    { name: 'english_level_basic', displayName: 'Nível Básico', displayNameEn: 'Basic Level' },
    { name: 'english_test_approved', displayName: 'Aprovado no Teste', displayNameEn: 'Test Approved', isApproval: true },
    { name: 'english_test_rejected', displayName: 'Reprovado no Teste', displayNameEn: 'Test Rejected', isRejection: true },
    { name: 'english_test_expired', displayName: 'Teste Expirado', displayNameEn: 'Test Expired' },
    { name: 'english_test_no_show', displayName: 'Não Realizou o Teste', displayNameEn: 'Test No Show' },
  ],
  
  // INTERVIEW TECHNICAL
  interview_technical: [
    { name: 'awaiting_technical_schedule', displayName: 'Aguardando Agenda Técnica', displayNameEn: 'Awaiting Technical Schedule', isWaiting: true, waitingFor: 'hr' },
    { name: 'technical_interview_scheduled', displayName: 'Entrevista Técnica Agendada', displayNameEn: 'Technical Interview Scheduled', isDefault: true },
    { name: 'technical_interview_confirmed', displayName: 'Entrevista Técnica Confirmada', displayNameEn: 'Technical Interview Confirmed' },
    { name: 'technical_interview_completed', displayName: 'Entrevista Técnica Realizada', displayNameEn: 'Technical Interview Completed' },
    { name: 'technical_test_sent', displayName: 'Teste Técnico Enviado', displayNameEn: 'Technical Test Sent' },
    { name: 'technical_test_in_progress', displayName: 'Teste Técnico em Andamento', displayNameEn: 'Technical Test in Progress' },
    { name: 'technical_test_received', displayName: 'Teste Técnico Recebido', displayNameEn: 'Technical Test Received' },
    { name: 'technical_test_evaluating', displayName: 'Teste Técnico em Avaliação', displayNameEn: 'Technical Test Evaluating' },
    { name: 'awaiting_technical_feedback', displayName: 'Aguardando Parecer Técnico', displayNameEn: 'Awaiting Technical Feedback', isWaiting: true, waitingFor: 'interviewer' },
    { name: 'technical_feedback_submitted', displayName: 'Parecer Técnico Enviado', displayNameEn: 'Technical Feedback Submitted' },
    { name: 'technical_approved', displayName: 'Aprovado em Técnica', displayNameEn: 'Technical Approved', isApproval: true },
    { name: 'technical_rejected', displayName: 'Reprovado em Técnica', displayNameEn: 'Technical Rejected', isRejection: true },
  ],
  
  // INTERVIEW MANAGER
  interview_manager: [
    { name: 'awaiting_manager1_schedule', displayName: 'Aguardando Agenda Gestor', displayNameEn: 'Awaiting Manager Schedule', isWaiting: true, waitingFor: 'manager' },
    { name: 'manager1_interview_scheduled', displayName: 'Entrevista Gestor Agendada', displayNameEn: 'Manager Interview Scheduled', isDefault: true },
    { name: 'manager1_interview_confirmed', displayName: 'Entrevista Gestor Confirmada', displayNameEn: 'Manager Interview Confirmed' },
    { name: 'manager1_interview_rescheduled', displayName: 'Entrevista Gestor Reagendada', displayNameEn: 'Manager Interview Rescheduled' },
    { name: 'manager1_interview_in_progress', displayName: 'Entrevista Gestor em Andamento', displayNameEn: 'Manager Interview in Progress' },
    { name: 'manager1_interview_completed', displayName: 'Entrevista Gestor Realizada', displayNameEn: 'Manager Interview Completed' },
    { name: 'manager1_interview_no_show', displayName: 'Não Compareceu Gestor', displayNameEn: 'Manager Interview No Show' },
    { name: 'awaiting_manager1_feedback', displayName: 'Aguardando Parecer Gestor', displayNameEn: 'Awaiting Manager Feedback', isWaiting: true, waitingFor: 'manager' },
    { name: 'manager1_feedback_submitted', displayName: 'Parecer Gestor Enviado', displayNameEn: 'Manager Feedback Submitted' },
    { name: 'manager1_interview_approved', displayName: 'Aprovado por Gestor', displayNameEn: 'Manager Interview Approved', isApproval: true },
    { name: 'manager1_interview_rejected', displayName: 'Reprovado por Gestor', displayNameEn: 'Manager Interview Rejected', isRejection: true },
  ],
  
  // INTERVIEW MANAGER 2
  interview_manager2: [
    { name: 'awaiting_manager2_schedule', displayName: 'Aguardando Agenda Gestor 2', displayNameEn: 'Awaiting Manager 2 Schedule', isWaiting: true, waitingFor: 'manager' },
    { name: 'manager2_interview_scheduled', displayName: 'Entrevista Gestor 2 Agendada', displayNameEn: 'Manager 2 Interview Scheduled', isDefault: true },
    { name: 'manager2_interview_confirmed', displayName: 'Entrevista Gestor 2 Confirmada', displayNameEn: 'Manager 2 Interview Confirmed' },
    { name: 'manager2_interview_completed', displayName: 'Entrevista Gestor 2 Realizada', displayNameEn: 'Manager 2 Interview Completed' },
    { name: 'awaiting_manager2_feedback', displayName: 'Aguardando Parecer Gestor 2', displayNameEn: 'Awaiting Manager 2 Feedback', isWaiting: true, waitingFor: 'manager' },
    { name: 'manager2_interview_approved', displayName: 'Aprovado por Gestor 2', displayNameEn: 'Manager 2 Interview Approved', isApproval: true },
    { name: 'manager2_interview_rejected', displayName: 'Reprovado por Gestor 2', displayNameEn: 'Manager 2 Interview Rejected', isRejection: true },
  ],
  
  // INTERVIEW FINAL
  interview_final: [
    { name: 'awaiting_final_schedule', displayName: 'Aguardando Agenda Final', displayNameEn: 'Awaiting Final Schedule', isWaiting: true, waitingFor: 'hr' },
    { name: 'final_interview_scheduled', displayName: 'Entrevista Final Agendada', displayNameEn: 'Final Interview Scheduled', isDefault: true },
    { name: 'final_interview_confirmed', displayName: 'Entrevista Final Confirmada', displayNameEn: 'Final Interview Confirmed' },
    { name: 'final_interview_completed', displayName: 'Entrevista Final Realizada', displayNameEn: 'Final Interview Completed' },
    { name: 'awaiting_final_feedback', displayName: 'Aguardando Parecer Final', displayNameEn: 'Awaiting Final Feedback', isWaiting: true, waitingFor: 'manager' },
    { name: 'final_interview_approved', displayName: 'Aprovado em Entrevista Final', displayNameEn: 'Final Interview Approved', isApproval: true },
    { name: 'final_interview_rejected', displayName: 'Reprovado em Entrevista Final', displayNameEn: 'Final Interview Rejected', isRejection: true },
  ],
  
  // REFERENCES
  references: [
    { name: 'references_requested', displayName: 'Referências Solicitadas', displayNameEn: 'References Requested', isDefault: true },
    { name: 'awaiting_references', displayName: 'Aguardando Referências', displayNameEn: 'Awaiting References', isWaiting: true, waitingFor: 'candidate' },
    { name: 'references_received', displayName: 'Referências Recebidas', displayNameEn: 'References Received' },
    { name: 'references_approved', displayName: 'Referências Aprovadas', displayNameEn: 'References Approved', isApproval: true },
    { name: 'references_concerns', displayName: 'Referências com Ressalvas', displayNameEn: 'References with Concerns' },
    { name: 'references_negative', displayName: 'Referências Negativas', displayNameEn: 'Negative References', isRejection: true },
    { name: 'background_check_started', displayName: 'Background Check Iniciado', displayNameEn: 'Background Check Started' },
    { name: 'background_check_approved', displayName: 'Background Check Aprovado', displayNameEn: 'Background Check Approved', isApproval: true },
    { name: 'background_check_rejected', displayName: 'Background Check Reprovado', displayNameEn: 'Background Check Rejected', isRejection: true },
  ],
  
  // OFFER
  offer: [
    { name: 'awaiting_internal_approval', displayName: 'Aguardando Aprovação Interna', displayNameEn: 'Awaiting Internal Approval', isWaiting: true, waitingFor: 'manager' },
    { name: 'offer_internally_approved', displayName: 'Proposta Aprovada Internamente', displayNameEn: 'Offer Internally Approved' },
    { name: 'preparing_offer', displayName: 'Preparando Proposta', displayNameEn: 'Preparing Offer', isDefault: true },
    { name: 'offer_sent', displayName: 'Proposta Enviada', displayNameEn: 'Offer Sent' },
    { name: 'offer_viewed', displayName: 'Proposta Visualizada', displayNameEn: 'Offer Viewed' },
    { name: 'negotiating', displayName: 'Em Negociação', displayNameEn: 'Negotiating' },
    { name: 'counter_offer_sent', displayName: 'Contraproposta Enviada', displayNameEn: 'Counter Offer Sent' },
    { name: 'awaiting_offer_response', displayName: 'Aguardando Resposta', displayNameEn: 'Awaiting Offer Response', isWaiting: true, waitingFor: 'candidate' },
    { name: 'offer_accepted', displayName: 'Proposta Aceita', displayNameEn: 'Offer Accepted', isApproval: true },
    { name: 'offer_expired', displayName: 'Proposta Expirada', displayNameEn: 'Offer Expired' },
  ],
  
  // HIRED
  hired: [
    { name: 'awaiting_admission_docs', displayName: 'Aguardando Documentos Admissionais', displayNameEn: 'Awaiting Admission Documents', isDefault: true, isWaiting: true, waitingFor: 'candidate' },
    { name: 'admission_docs_received', displayName: 'Documentos Admissionais Recebidos', displayNameEn: 'Admission Documents Received' },
    { name: 'admission_exam_scheduled', displayName: 'Exame Admissional Agendado', displayNameEn: 'Admission Exam Scheduled' },
    { name: 'admission_exam_completed', displayName: 'Exame Admissional Realizado', displayNameEn: 'Admission Exam Completed' },
    { name: 'admission_exam_approved', displayName: 'Exame Admissional Aprovado', displayNameEn: 'Admission Exam Approved', isApproval: true },
    { name: 'admission_exam_failed', displayName: 'Exame Admissional Inapto', displayNameEn: 'Admission Exam Failed', isRejection: true },
    { name: 'contract_preparing', displayName: 'Contrato em Elaboração', displayNameEn: 'Contract Preparing' },
    { name: 'contract_sent', displayName: 'Contrato Enviado', displayNameEn: 'Contract Sent' },
    { name: 'contract_signed', displayName: 'Contrato Assinado', displayNameEn: 'Contract Signed', isApproval: true },
    { name: 'onboarding_scheduled', displayName: 'Onboarding Agendado', displayNameEn: 'Onboarding Scheduled' },
    { name: 'onboarding_in_progress', displayName: 'Onboarding em Andamento', displayNameEn: 'Onboarding in Progress' },
    { name: 'onboarding_completed', displayName: 'Onboarding Concluído', displayNameEn: 'Onboarding Completed', isApproval: true },
    { name: 'started_work', displayName: 'Iniciou Trabalho', displayNameEn: 'Started Work', isApproval: true },
  ],
  
  // STANDBY
  standby: [
    { name: 'future_talent', displayName: 'Talento para Futuro', displayNameEn: 'Future Talent', isDefault: true },
    { name: 'better_other_role', displayName: 'Melhor para Outra Vaga', displayNameEn: 'Better for Another Role' },
    { name: 'awaiting_candidate_availability', displayName: 'Aguardando Disponibilidade', displayNameEn: 'Awaiting Candidate Availability', isWaiting: true, waitingFor: 'candidate' },
    { name: 'awaiting_senior_role', displayName: 'Aguardando Vaga Sênior', displayNameEn: 'Awaiting Senior Role' },
    { name: 'awaiting_junior_role', displayName: 'Aguardando Vaga Júnior', displayNameEn: 'Awaiting Junior Role' },
    { name: 'paused_by_candidate', displayName: 'Processo Pausado pelo Candidato', displayNameEn: 'Paused by Candidate' },
    { name: 'paused_by_company', displayName: 'Processo Pausado pela Empresa', displayNameEn: 'Paused by Company' },
    { name: 'reengage_30_days', displayName: 'Re-engajar em 30 Dias', displayNameEn: 'Re-engage in 30 Days' },
    { name: 'reengage_3_months', displayName: 'Re-engajar em 3 Meses', displayNameEn: 'Re-engage in 3 Months' },
    { name: 'reengage_6_months', displayName: 'Re-engajar em 6 Meses', displayNameEn: 'Re-engage in 6 Months' },
    { name: 'awaiting_budget', displayName: 'Aguardando Orçamento/Headcount', displayNameEn: 'Awaiting Budget' },
    { name: 'awaiting_scope_definition', displayName: 'Aguardando Definição de Escopo', displayNameEn: 'Awaiting Scope Definition' },
    { name: 'candidate_in_probation', displayName: 'Candidato em Período de Experiência', displayNameEn: 'Candidate in Probation' },
  ],
}

// ==================== REJECTION REASONS ====================

export const REJECTION_REASONS: RejectionReason[] = [
  // Qualification
  { code: 'lacking_experience', displayName: 'Falta de Experiência', displayNameEn: 'Lacking Experience', category: 'qualification' },
  { code: 'under_qualified', displayName: 'Subqualificado', displayNameEn: 'Under Qualified', category: 'qualification' },
  { code: 'over_qualified', displayName: 'Sobrequalificado', displayNameEn: 'Over Qualified', category: 'qualification' },
  { code: 'lacking_technical_skills', displayName: 'Habilidades Técnicas Insuficientes', displayNameEn: 'Lacking Technical Skills', category: 'qualification' },
  { code: 'education_mismatch', displayName: 'Formação Incompatível', displayNameEn: 'Education Mismatch', category: 'qualification' },
  { code: 'missing_certification', displayName: 'Certificação Ausente', displayNameEn: 'Missing Certification', category: 'qualification' },
  { code: 'language_insufficient', displayName: 'Idioma Insuficiente', displayNameEn: 'Language Insufficient', category: 'qualification' },
  { code: 'tools_insufficient', displayName: 'Conhecimento de Ferramentas Insuficiente', displayNameEn: 'Tools Knowledge Insufficient', category: 'qualification' },
  
  // Cultural
  { code: 'cultural_mismatch', displayName: 'Não Aprovado Culturalmente', displayNameEn: 'Cultural Mismatch', category: 'cultural' },
  { code: 'poor_communication', displayName: 'Comunicação Inadequada', displayNameEn: 'Poor Communication', category: 'cultural' },
  { code: 'inadequate_attitude', displayName: 'Postura Inadequada na Entrevista', displayNameEn: 'Inadequate Attitude', category: 'cultural' },
  { code: 'lack_professionalism', displayName: 'Falta de Profissionalismo', displayNameEn: 'Lack of Professionalism', category: 'cultural' },
  { code: 'lack_of_interest', displayName: 'Não Demonstrou Interesse', displayNameEn: 'Lack of Interest', category: 'cultural' },
  { code: 'misaligned_expectations', displayName: 'Expectativas Desalinhadas', displayNameEn: 'Misaligned Expectations', category: 'cultural' },
  
  // Logistics
  { code: 'location_mismatch', displayName: 'Localização Incompatível', displayNameEn: 'Location Mismatch', category: 'logistics' },
  { code: 'work_model_mismatch', displayName: 'Modelo de Trabalho Incompatível', displayNameEn: 'Work Model Mismatch', category: 'logistics' },
  { code: 'visa_required', displayName: 'Necessita Visto/Patrocínio', displayNameEn: 'Visa Required', category: 'logistics' },
  { code: 'start_date_mismatch', displayName: 'Disponibilidade de Data Incompatível', displayNameEn: 'Start Date Mismatch', category: 'logistics' },
  { code: 'schedule_mismatch', displayName: 'Horário/Jornada Incompatível', displayNameEn: 'Schedule Mismatch', category: 'logistics' },
  { code: 'travel_requirements_mismatch', displayName: 'Viagens Incompatíveis', displayNameEn: 'Travel Requirements Mismatch', category: 'logistics' },
  
  // Compensation
  { code: 'salary_above_budget', displayName: 'Expectativa Salarial Acima do Budget', displayNameEn: 'Salary Above Budget', category: 'compensation' },
  { code: 'benefits_mismatch', displayName: 'Expectativa de Benefícios Incompatível', displayNameEn: 'Benefits Mismatch', category: 'compensation' },
  { code: 'compensation_not_competitive', displayName: 'Pacote Total Não Competitivo', displayNameEn: 'Compensation Not Competitive', category: 'compensation' },
  
  // Process
  { code: 'interview_no_show', displayName: 'Não Compareceu à Entrevista', displayNameEn: 'Interview No Show', category: 'process' },
  { code: 'test_no_show', displayName: 'Não Compareceu ao Teste', displayNameEn: 'Test No Show', category: 'process' },
  { code: 'withdrew', displayName: 'Desistiu do Processo', displayNameEn: 'Withdrew', category: 'process' },
  { code: 'unresponsive', displayName: 'Não Respondeu Tentativas de Contato', displayNameEn: 'Unresponsive', category: 'process' },
  { code: 'incomplete_documentation', displayName: 'Documentação Incompleta', displayNameEn: 'Incomplete Documentation', category: 'process' },
  { code: 'failed_technical_test', displayName: 'Reprovado em Teste Técnico', displayNameEn: 'Failed Technical Test', category: 'process' },
  { code: 'failed_behavioral_test', displayName: 'Reprovado em Teste Comportamental', displayNameEn: 'Failed Behavioral Test', category: 'process' },
  { code: 'negative_references', displayName: 'Referências Negativas', displayNameEn: 'Negative References', category: 'process' },
  { code: 'failed_background_check', displayName: 'Background Check Reprovado', displayNameEn: 'Failed Background Check', category: 'process' },
  { code: 'failed_admission_exam', displayName: 'Exame Admissional Inapto', displayNameEn: 'Failed Admission Exam', category: 'process' },
  
  // Business Decision
  { code: 'another_candidate_selected', displayName: 'Outro Candidato Selecionado', displayNameEn: 'Another Candidate Selected', category: 'business_decision' },
  { code: 'position_cancelled', displayName: 'Vaga Cancelada', displayNameEn: 'Position Cancelled', category: 'business_decision' },
  { code: 'position_frozen', displayName: 'Vaga Congelada', displayNameEn: 'Position Frozen', category: 'business_decision' },
  { code: 'internal_hire', displayName: 'Contratação Interna', displayNameEn: 'Internal Hire', category: 'business_decision' },
  { code: 'budget_insufficient', displayName: 'Budget Insuficiente', displayNameEn: 'Budget Insufficient', category: 'business_decision' },
  { code: 'org_restructuring', displayName: 'Reestruturação Organizacional', displayNameEn: 'Org Restructuring', category: 'business_decision' },
]

// ==================== OFFER DECLINE REASONS ====================

export const OFFER_DECLINE_REASONS: OfferDeclineReason[] = [
  { code: 'accepted_other_offer', displayName: 'Aceitou Proposta de Outra Empresa', displayNameEn: 'Accepted Other Offer' },
  { code: 'salary_below_expectation', displayName: 'Salário Abaixo do Esperado', displayNameEn: 'Salary Below Expectation' },
  { code: 'insufficient_benefits', displayName: 'Benefícios Insuficientes', displayNameEn: 'Insufficient Benefits' },
  { code: 'work_model_not_accepted', displayName: 'Modelo de Trabalho Não Aceito', displayNameEn: 'Work Model Not Accepted' },
  { code: 'location_not_accepted', displayName: 'Localização Não Aceita', displayNameEn: 'Location Not Accepted' },
  { code: 'accepted_counter_offer', displayName: 'Aceitou Contraproposta do Empregador Atual', displayNameEn: 'Accepted Counter Offer' },
  { code: 'personal_family_reasons', displayName: 'Motivos Pessoais/Familiares', displayNameEn: 'Personal/Family Reasons' },
  { code: 'culture_not_aligned', displayName: 'Não se Identificou com Cultura', displayNameEn: 'Culture Not Aligned' },
  { code: 'better_career_opportunity', displayName: 'Melhor Oportunidade de Carreira', displayNameEn: 'Better Career Opportunity' },
  { code: 'company_response_timing', displayName: 'Tempo de Resposta da Empresa', displayNameEn: 'Company Response Timing' },
  { code: 'personal_plans_changed', displayName: 'Mudança de Planos Pessoais', displayNameEn: 'Personal Plans Changed' },
  { code: 'health_issues', displayName: 'Questões de Saúde', displayNameEn: 'Health Issues' },
]

// ==================== TEST & ASSESSMENT STATUSES ====================

export const TEST_STATUSES: Record<string, SubStatus[]> = {
  // Technical Test
  technical_test: [
    { name: 'technical_test_preparing', displayName: 'Preparando Teste', displayNameEn: 'Preparing Test' },
    { name: 'technical_test_sent', displayName: 'Teste Enviado', displayNameEn: 'Test Sent', isDefault: true },
    { name: 'technical_test_viewed', displayName: 'Teste Visualizado', displayNameEn: 'Test Viewed' },
    { name: 'technical_test_awaiting_start', displayName: 'Aguardando Início', displayNameEn: 'Awaiting Start', isWaiting: true, waitingFor: 'candidate' },
    { name: 'technical_test_in_progress', displayName: 'Em Andamento', displayNameEn: 'In Progress' },
    { name: 'technical_test_paused', displayName: 'Pausado', displayNameEn: 'Paused' },
    { name: 'technical_test_abandoned', displayName: 'Abandonado', displayNameEn: 'Abandoned' },
    { name: 'technical_test_expired', displayName: 'Expirado', displayNameEn: 'Expired' },
    { name: 'technical_test_submitted', displayName: 'Submetido', displayNameEn: 'Submitted' },
    { name: 'technical_test_received', displayName: 'Recebido', displayNameEn: 'Received' },
    { name: 'technical_test_late_submission', displayName: 'Entrega Atrasada', displayNameEn: 'Late Submission' },
    { name: 'technical_test_evaluating', displayName: 'Em Avaliação', displayNameEn: 'Evaluating' },
    { name: 'awaiting_technical_correction', displayName: 'Aguardando Correção', displayNameEn: 'Awaiting Correction', isWaiting: true, waitingFor: 'interviewer' },
    { name: 'technical_test_corrected', displayName: 'Corrigido', displayNameEn: 'Corrected' },
    { name: 'technical_test_approved', displayName: 'Aprovado', displayNameEn: 'Approved', isApproval: true },
    { name: 'technical_test_approved_concerns', displayName: 'Aprovado com Ressalvas', displayNameEn: 'Approved with Concerns' },
    { name: 'technical_test_rejected', displayName: 'Reprovado', displayNameEn: 'Rejected', isRejection: true },
    { name: 'technical_test_borderline', displayName: 'Nota Limítrofe', displayNameEn: 'Borderline Score' },
  ],
  
  // English Test
  english_test: [
    { name: 'english_test_sent', displayName: 'Teste Enviado', displayNameEn: 'Test Sent', isDefault: true },
    { name: 'english_test_viewed', displayName: 'Teste Visualizado', displayNameEn: 'Test Viewed' },
    { name: 'english_test_awaiting_start', displayName: 'Aguardando Início', displayNameEn: 'Awaiting Start', isWaiting: true, waitingFor: 'candidate' },
    { name: 'english_test_in_progress', displayName: 'Em Andamento', displayNameEn: 'In Progress' },
    { name: 'english_test_submitted', displayName: 'Submetido', displayNameEn: 'Submitted' },
    { name: 'english_test_expired', displayName: 'Expirado', displayNameEn: 'Expired' },
    { name: 'english_test_evaluating', displayName: 'Em Avaliação', displayNameEn: 'Evaluating' },
    { name: 'english_test_corrected', displayName: 'Corrigido', displayNameEn: 'Corrected' },
    { name: 'english_level_basic', displayName: 'Nível Básico (A1-A2)', displayNameEn: 'Basic Level (A1-A2)' },
    { name: 'english_level_intermediate', displayName: 'Nível Intermediário (B1-B2)', displayNameEn: 'Intermediate Level (B1-B2)' },
    { name: 'english_level_advanced', displayName: 'Nível Avançado (C1)', displayNameEn: 'Advanced Level (C1)' },
    { name: 'english_level_fluent', displayName: 'Nível Fluente (C2)', displayNameEn: 'Fluent Level (C2)' },
    { name: 'english_level_native', displayName: 'Nativo', displayNameEn: 'Native' },
    { name: 'english_test_approved', displayName: 'Aprovado', displayNameEn: 'Approved', isApproval: true },
    { name: 'english_test_rejected', displayName: 'Reprovado', displayNameEn: 'Rejected', isRejection: true },
  ],
  
  // Behavioral Assessment
  behavioral_assessment: [
    { name: 'behavioral_assessment_sent', displayName: 'Assessment Enviado', displayNameEn: 'Assessment Sent', isDefault: true },
    { name: 'behavioral_assessment_viewed', displayName: 'Assessment Visualizado', displayNameEn: 'Assessment Viewed' },
    { name: 'behavioral_assessment_awaiting', displayName: 'Aguardando Início', displayNameEn: 'Awaiting Start', isWaiting: true, waitingFor: 'candidate' },
    { name: 'behavioral_assessment_in_progress', displayName: 'Em Andamento', displayNameEn: 'In Progress' },
    { name: 'behavioral_assessment_paused', displayName: 'Pausado', displayNameEn: 'Paused' },
    { name: 'behavioral_assessment_submitted', displayName: 'Submetido', displayNameEn: 'Submitted' },
    { name: 'behavioral_assessment_expired', displayName: 'Expirado', displayNameEn: 'Expired' },
    { name: 'behavioral_assessment_incomplete', displayName: 'Incompleto', displayNameEn: 'Incomplete' },
    { name: 'behavioral_assessment_analyzing', displayName: 'Em Análise', displayNameEn: 'Analyzing' },
    { name: 'behavioral_report_generated', displayName: 'Relatório Gerado', displayNameEn: 'Report Generated' },
    { name: 'behavioral_awaiting_interpretation', displayName: 'Aguardando Interpretação', displayNameEn: 'Awaiting Interpretation', isWaiting: true, waitingFor: 'hr' },
    { name: 'behavioral_profile_aligned', displayName: 'Perfil Alinhado', displayNameEn: 'Profile Aligned', isApproval: true },
    { name: 'behavioral_profile_partial', displayName: 'Perfil Parcialmente Alinhado', displayNameEn: 'Profile Partially Aligned' },
    { name: 'behavioral_profile_not_aligned', displayName: 'Perfil Não Alinhado', displayNameEn: 'Profile Not Aligned', isRejection: true },
  ],
  
  // Case Study
  case_study: [
    { name: 'case_study_preparing', displayName: 'Preparando Case', displayNameEn: 'Preparing Case' },
    { name: 'case_study_sent', displayName: 'Case Enviado', displayNameEn: 'Case Sent', isDefault: true },
    { name: 'case_study_viewed', displayName: 'Case Visualizado', displayNameEn: 'Case Viewed' },
    { name: 'case_instructions_sent', displayName: 'Instruções Enviadas', displayNameEn: 'Instructions Sent' },
    { name: 'case_study_awaiting_start', displayName: 'Aguardando Início', displayNameEn: 'Awaiting Start', isWaiting: true, waitingFor: 'candidate' },
    { name: 'case_study_in_progress', displayName: 'Em Desenvolvimento', displayNameEn: 'In Progress' },
    { name: 'case_study_questions', displayName: 'Dúvidas sobre o Case', displayNameEn: 'Case Questions' },
    { name: 'case_questions_answered', displayName: 'Dúvidas Respondidas', displayNameEn: 'Questions Answered' },
    { name: 'case_study_submitted', displayName: 'Case Submetido', displayNameEn: 'Case Submitted' },
    { name: 'case_study_received', displayName: 'Case Recebido', displayNameEn: 'Case Received' },
    { name: 'case_study_late', displayName: 'Entrega Atrasada', displayNameEn: 'Late Submission' },
    { name: 'case_study_not_submitted', displayName: 'Não Entregue', displayNameEn: 'Not Submitted' },
    { name: 'case_presentation_scheduled', displayName: 'Apresentação Agendada', displayNameEn: 'Presentation Scheduled' },
    { name: 'case_presentation_confirmed', displayName: 'Apresentação Confirmada', displayNameEn: 'Presentation Confirmed' },
    { name: 'case_presentation_completed', displayName: 'Apresentação Realizada', displayNameEn: 'Presentation Completed' },
    { name: 'awaiting_case_feedback', displayName: 'Aguardando Feedback', displayNameEn: 'Awaiting Feedback', isWaiting: true, waitingFor: 'interviewer' },
    { name: 'case_study_evaluating', displayName: 'Em Avaliação', displayNameEn: 'Evaluating' },
    { name: 'case_study_evaluated', displayName: 'Avaliado', displayNameEn: 'Evaluated' },
    { name: 'case_study_approved', displayName: 'Aprovado', displayNameEn: 'Approved', isApproval: true },
    { name: 'case_study_approved_concerns', displayName: 'Aprovado com Ressalvas', displayNameEn: 'Approved with Concerns' },
    { name: 'case_study_rejected', displayName: 'Reprovado', displayNameEn: 'Rejected', isRejection: true },
  ],
  
  // Cognitive Tests
  cognitive_test: [
    { name: 'logic_test_sent', displayName: 'Teste Lógico Enviado', displayNameEn: 'Logic Test Sent', isDefault: true },
    { name: 'logic_test_in_progress', displayName: 'Teste Lógico em Andamento', displayNameEn: 'Logic Test in Progress' },
    { name: 'logic_test_submitted', displayName: 'Teste Lógico Submetido', displayNameEn: 'Logic Test Submitted' },
    { name: 'logic_test_approved', displayName: 'Teste Lógico Aprovado', displayNameEn: 'Logic Test Approved', isApproval: true },
    { name: 'logic_test_rejected', displayName: 'Teste Lógico Reprovado', displayNameEn: 'Logic Test Rejected', isRejection: true },
    { name: 'numerical_test_sent', displayName: 'Teste Numérico Enviado', displayNameEn: 'Numerical Test Sent' },
    { name: 'numerical_test_approved', displayName: 'Teste Numérico Aprovado', displayNameEn: 'Numerical Test Approved', isApproval: true },
    { name: 'verbal_test_sent', displayName: 'Teste Verbal Enviado', displayNameEn: 'Verbal Test Sent' },
    { name: 'verbal_test_approved', displayName: 'Teste Verbal Aprovado', displayNameEn: 'Verbal Test Approved', isApproval: true },
    { name: 'attention_test_sent', displayName: 'Teste de Atenção Enviado', displayNameEn: 'Attention Test Sent' },
    { name: 'attention_test_approved', displayName: 'Teste de Atenção Aprovado', displayNameEn: 'Attention Test Approved', isApproval: true },
  ],
  
  // Video Interview
  video_interview: [
    { name: 'video_interview_sent', displayName: 'Vídeo Entrevista Enviada', displayNameEn: 'Video Interview Sent', isDefault: true },
    { name: 'video_interview_viewed', displayName: 'Vídeo Entrevista Visualizada', displayNameEn: 'Video Interview Viewed' },
    { name: 'video_interview_awaiting', displayName: 'Aguardando Gravação', displayNameEn: 'Awaiting Recording', isWaiting: true, waitingFor: 'candidate' },
    { name: 'video_interview_recording', displayName: 'Gravação em Andamento', displayNameEn: 'Recording in Progress' },
    { name: 'video_interview_submitted', displayName: 'Vídeo Submetido', displayNameEn: 'Video Submitted' },
    { name: 'video_interview_expired', displayName: 'Vídeo Expirado', displayNameEn: 'Video Expired' },
    { name: 'video_interview_evaluating', displayName: 'Em Avaliação', displayNameEn: 'Evaluating' },
    { name: 'video_interview_approved', displayName: 'Aprovado', displayNameEn: 'Approved', isApproval: true },
    { name: 'video_interview_rejected', displayName: 'Reprovado', displayNameEn: 'Rejected', isRejection: true },
  ],
}

// ==================== DOCUMENT COLLECTION STATUSES ====================

export const DOCUMENT_STATUSES: SubStatus[] = [
  // Registration
  { name: 'registration_started', displayName: 'Cadastro Iniciado', displayNameEn: 'Registration Started' },
  { name: 'registration_incomplete', displayName: 'Cadastro Incompleto', displayNameEn: 'Registration Incomplete' },
  { name: 'registration_complete', displayName: 'Cadastro Completo', displayNameEn: 'Registration Complete', isApproval: true },
  { name: 'data_validating', displayName: 'Dados em Validação', displayNameEn: 'Data Validating' },
  { name: 'data_validated', displayName: 'Dados Validados', displayNameEn: 'Data Validated', isApproval: true },
  { name: 'data_inconsistent', displayName: 'Dados com Inconsistência', displayNameEn: 'Data Inconsistent' },
  { name: 'data_update_requested', displayName: 'Atualização Solicitada', displayNameEn: 'Update Requested', isWaiting: true, waitingFor: 'candidate' },
  { name: 'data_updated', displayName: 'Dados Atualizados', displayNameEn: 'Data Updated' },
  
  // CV
  { name: 'cv_not_attached', displayName: 'CV Não Anexado', displayNameEn: 'CV Not Attached' },
  { name: 'cv_attached', displayName: 'CV Anexado', displayNameEn: 'CV Attached' },
  { name: 'cv_outdated', displayName: 'CV Desatualizado', displayNameEn: 'CV Outdated' },
  { name: 'cv_update_requested', displayName: 'Atualização de CV Solicitada', displayNameEn: 'CV Update Requested', isWaiting: true, waitingFor: 'candidate' },
  { name: 'cv_updated', displayName: 'CV Atualizado', displayNameEn: 'CV Updated' },
  
  // LinkedIn/Portfolio
  { name: 'linkedin_missing', displayName: 'LinkedIn Não Informado', displayNameEn: 'LinkedIn Missing' },
  { name: 'linkedin_provided', displayName: 'LinkedIn Informado', displayNameEn: 'LinkedIn Provided' },
  { name: 'linkedin_validated', displayName: 'LinkedIn Validado', displayNameEn: 'LinkedIn Validated', isApproval: true },
  { name: 'portfolio_missing', displayName: 'Portfólio Não Informado', displayNameEn: 'Portfolio Missing' },
  { name: 'portfolio_provided', displayName: 'Portfólio Informado', displayNameEn: 'Portfolio Provided' },
  { name: 'github_provided', displayName: 'GitHub Informado', displayNameEn: 'GitHub Provided' },
  
  // Personal Documents
  { name: 'personal_docs_requested', displayName: 'Documentos Solicitados', displayNameEn: 'Documents Requested' },
  { name: 'awaiting_personal_docs', displayName: 'Aguardando Documentos', displayNameEn: 'Awaiting Documents', isWaiting: true, waitingFor: 'candidate' },
  { name: 'personal_docs_received', displayName: 'Documentos Recebidos', displayNameEn: 'Documents Received' },
  { name: 'personal_docs_validating', displayName: 'Documentos em Validação', displayNameEn: 'Documents Validating' },
  { name: 'personal_docs_approved', displayName: 'Documentos Aprovados', displayNameEn: 'Documents Approved', isApproval: true },
  { name: 'personal_docs_pending', displayName: 'Documentos Pendentes', displayNameEn: 'Documents Pending' },
  { name: 'personal_docs_expired', displayName: 'Documentos Vencidos', displayNameEn: 'Documents Expired' },
  { name: 'personal_docs_invalid', displayName: 'Documentos Inválidos', displayNameEn: 'Documents Invalid', isRejection: true },
  
  // Certificates
  { name: 'certificates_requested', displayName: 'Certificados Solicitados', displayNameEn: 'Certificates Requested' },
  { name: 'certificates_received', displayName: 'Certificados Recebidos', displayNameEn: 'Certificates Received' },
  { name: 'certificates_validated', displayName: 'Certificados Validados', displayNameEn: 'Certificates Validated', isApproval: true },
  { name: 'diploma_requested', displayName: 'Diploma Solicitado', displayNameEn: 'Diploma Requested' },
  { name: 'diploma_received', displayName: 'Diploma Recebido', displayNameEn: 'Diploma Received' },
  { name: 'diploma_validated', displayName: 'Diploma Validado', displayNameEn: 'Diploma Validated', isApproval: true },
  { name: 'address_proof_requested', displayName: 'Comprovante de Residência Solicitado', displayNameEn: 'Address Proof Requested' },
  { name: 'address_proof_received', displayName: 'Comprovante de Residência Recebido', displayNameEn: 'Address Proof Received' },
]

// ==================== CANDIDATE SOURCES ====================

export const CANDIDATE_SOURCES: CandidateSource[] = [
  { id: 'website', name: 'website', displayName: 'Website', icon: 'globe', color: 'var(--lia-text-secondary)' },
  { id: 'linkedin', name: 'linkedin', displayName: 'LinkedIn', icon: 'linkedin', color: '#0A66C2' }, // brand color — isento
  { id: 'indeed', name: 'indeed', displayName: 'Indeed', icon: 'briefcase', color: 'var(--lia-text-secondary)' },
  { id: 'glassdoor', name: 'glassdoor', displayName: 'Glassdoor', icon: 'building', color: 'var(--lia-text-secondary)' },
  { id: 'referral', name: 'referral', displayName: 'Indicação', icon: 'users', color: 'var(--lia-text-primary)' },
  { id: 'internal', name: 'internal', displayName: 'Interno', icon: 'home', color: 'var(--lia-text-primary)' },
  { id: 'agency', name: 'agency', displayName: 'Agência', icon: 'briefcase', color: 'var(--lia-text-secondary)' },
  { id: 'university', name: 'university', displayName: 'Universidade', icon: 'graduation-cap', color: 'var(--lia-text-secondary)' },
  { id: 'event', name: 'event', displayName: 'Evento', icon: 'calendar', color: 'var(--lia-text-tertiary)' },
  { id: 'ats_gupy', name: 'ats_gupy', displayName: 'Gupy', icon: 'database', color: 'var(--lia-text-secondary)' },
  { id: 'ats_greenhouse', name: 'ats_greenhouse', displayName: 'Greenhouse', icon: 'database', color: 'var(--lia-text-secondary)' },
  { id: 'ats_lever', name: 'ats_lever', displayName: 'Lever', icon: 'database', color: 'var(--lia-text-primary)' },
  { id: 'pearch', name: 'pearch', displayName: 'Pearch AI', icon: 'search', color: 'var(--wedo-cyan)' },
  { id: 'manual', name: 'manual', displayName: 'Manual', icon: 'edit', color: 'var(--lia-text-secondary)' },
  { id: 'other', name: 'other', displayName: 'Outro', icon: 'more-horizontal', color: 'var(--lia-text-tertiary)' },
]

// ==================== HELPER FUNCTIONS ====================

export function getCandidateSourceById(sourceId: string): CandidateSource | undefined {
  return CANDIDATE_SOURCES.find(source => source.id === sourceId)
}

export function isApplicationSource(sourceId: string): boolean {
  const applicationSources = ['website', 'linkedin', 'indeed', 'glassdoor']
  return applicationSources.includes(sourceId)
}

export function getRejectionReasonsByCategory(category: StatusCategory): RejectionReason[] {
  return REJECTION_REASONS.filter(r => r.category === category)
}

// ============================================================================
// WT-2022 P0.SUB_STATUSES — adapter helpers (hook canonical snake_case → legacy)
// ============================================================================

/**
 * Shape minimo de SubStatus canonical recebido pelo hook useRecruitmentStages
 * (vem de /api/backend-proxy/company-pipeline, snake_case).
 *
 * Mantenha em sincronia com CanonicalSubStatus em
 * @/components/settings/recruitment-journey.types.ts (interface SubStatus).
 * Schema-sync TS pattern: campo novo num lado exige campo no outro.
 */
export interface HookSubStatus {
  id?: string
  stage_id?: string
  name: string
  display_name?: string
  description?: string
  is_active?: boolean
  is_default?: boolean
  is_waiting?: boolean
  waiting_for?: string
  sla_hours?: number
  sub_status_order?: number
  color?: string
  icon?: string
  // Campos heuristicos opcionais — backend pode nao mandar; resolveSubStatusFlags faz fallback
  is_approval?: boolean
  is_rejection?: boolean
  category?: StatusCategory
}

/**
 * Resolve isApproval/isRejection a partir do nome canonical e flags presentes.
 * Backend (recruitment_sub_statuses) hoje nao tem campos is_approval/is_rejection
 * explicitos — eles vivem so no SUB_STATUSES hardcoded. Pra back-compat,
 * checamos a lista canonical hardcoded primeiro; se nao bater, marcamos false.
 */
function resolveSubStatusFlags(name: string, stageHint?: string): {
  isApproval: boolean
  isRejection: boolean
} {
  if (stageHint) {
    const canonical = SUB_STATUSES[stageHint]?.find((s) => s.name === name)
    if (canonical) {
      return {
        isApproval: canonical.isApproval ?? false,
        isRejection: canonical.isRejection ?? false,
      }
    }
  }
  // fallback: varre todos os stages
  for (const list of Object.values(SUB_STATUSES)) {
    const found = list.find((s) => s.name === name)
    if (found) {
      return {
        isApproval: found.isApproval ?? false,
        isRejection: found.isRejection ?? false,
      }
    }
  }
  return { isApproval: false, isRejection: false }
}

/**
 * Normaliza um sub-status canonical (snake_case do backend) pro shape legacy
 * (camelCase usado por SUB_STATUSES hardcoded + consumers como InteractiveSubStatusCell).
 *
 * @example
 *   const { legacySubStatuses } = useRecruitmentStages()
 *   const sourcing = legacySubStatuses["sourcing"]
 *   sourcing[0].displayName // "Identificado"
 */
export function normalizeSubStatusFromHook(
  ss: HookSubStatus,
  stageHint?: string,
): SubStatus {
  const flags = resolveSubStatusFlags(ss.name, stageHint)
  // waiting_for canonical Python values: candidate|interviewer|manager|hr|system
  const waitingFor =
    ss.waiting_for === "candidate" ||
    ss.waiting_for === "interviewer" ||
    ss.waiting_for === "manager" ||
    ss.waiting_for === "hr" ||
    ss.waiting_for === "system"
      ? ss.waiting_for
      : undefined
  return {
    name: ss.name,
    displayName: ss.display_name ?? ss.name,
    isDefault: ss.is_default ?? false,
    isWaiting: ss.is_waiting ?? false,
    isApproval: ss.is_approval ?? flags.isApproval,
    isRejection: ss.is_rejection ?? flags.isRejection,
    waitingFor,
    category: ss.category,
    icon: ss.icon,
    color: ss.color,
  }
}

/**
 * Normaliza o mapa {stageName -> HookSubStatus[]} pro shape legacy
 * {stageName -> SubStatus[]} (camelCase). Use no hook canonical.
 */
export function normalizeSubStatusesFromHook(
  byStage: Record<string, HookSubStatus[]>,
): Record<string, SubStatus[]> {
  const result: Record<string, SubStatus[]> = {}
  for (const [stageName, list] of Object.entries(byStage)) {
    result[stageName] = list.map((ss) => normalizeSubStatusFromHook(ss, stageName))
  }
  return result
}
