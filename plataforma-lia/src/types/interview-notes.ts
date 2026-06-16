/**
 * Interview Notes System Types
 * Tipos para o sistema de Notas de Entrevista da plataforma LIA
 * 
 * Suporta a estrutura de Score Card WSI com 4 blocos:
 * - Technical (peso: 0.50)
 * - Behavioral (peso: 0.20)
 * - Gap Analysis (peso: 0.15)
 * - Contextual (peso: 0.15)
 */

/**
 * Tipo de bloco de questões - Estrutura WSI com 4 blocos
 */
export type QuestionBlockType = 'technical' | 'behavioral' | 'gap_analysis' | 'contextual';

/**
 * Bloco de questões agrupadas por tipo e peso
 */
export interface QuestionBlock {
  type: QuestionBlockType;
  label: string;
  weight: number; // 0.50, 0.20, 0.15, 0.15
  questions: InterviewNoteQuestion[];
  subtotalScore?: number;
}

/**
 * Score WSI - Resultado do cálculo de avaliação
 */
export interface WSIScore {
  technicalScore: number;
  behavioralScore: number;
  gapAnalysisScore: number;
  contextualScore: number;
  totalWSI: number;
  decision: 'approved' | 'human_review' | 'rejected';
  decisionLabel: string;
}

/**
 * Pergunta individual da entrevista
 */
export interface InterviewNoteQuestion {
  id: string;
  text: string;
  category: 'vaga' | 'gap_analysis' | 'fit_cultural' | 'custom';
  source: string;
  starRating: number | null;
  likertRating:
    | 'insatisfatorio'
    | 'abaixo_esperado'
    | 'esperado'
    | 'acima_esperado'
    | 'excelente'
    | null;
  notes: string;
  skipped: boolean;
  blockType?: QuestionBlockType; // A qual bloco WSI pertence
  skillId?: string; // ID da skill vinculada (para questões técnicas/comportamentais)
  skillName?: string; // Nome da skill
}

/**
 * Nota de entrevista completa
 */
export interface InterviewNote {
  id: string;
  candidateId: string;
  candidateName: string;
  jobId: string | null;
  jobTitle: string | null;
  scheduledInterviewId: string | null;
  interviewId?: string; // ID da reunião Teams/Meet para análise
  interviewType: 'scheduled' | 'ad_hoc';
  interviewDate: string;
  recruiterId: string;
  recruiterName: string;
  questions: InterviewNoteQuestion[];
  blocks?: QuestionBlock[]; // Estrutura organizada por blocos WSI
  generalNotes: string;
  transcription: string | null;
  transcriptionSource: 'teams' | 'meet' | 'manual' | null;
  liaParecer: string | null;
  liaParecerEditado: boolean;
  recommendation: 'approve' | 'reject' | 'pending' | null;
  nextStage: string | null;
  feedbackSent: boolean;
  feedbackScheduledFor: string | null;
  status: 'draft' | 'completed';
  wsiScore?: WSIScore; // Score calculado da avaliação WSI
  createdAt: string;
  updatedAt: string;
}

/**
 * Dados do formulário para criação/edição de notas de entrevista
 */
export interface InterviewNoteFormData {
  id?: string;
  candidateId: string;
  candidateName?: string;
  jobId?: string | null;
  jobTitle?: string | null;
  scheduledInterviewId?: string | null;
  interviewType?: 'scheduled' | 'ad_hoc';
  interviewDate?: string;
  recruiterId?: string;
  recruiterName?: string;
  questions?: InterviewNoteQuestion[];
  blocks?: QuestionBlock[];
  generalNotes?: string;
  transcription?: string | null;
  transcriptionSource?: 'teams' | 'meet' | 'manual' | null;
  liaParecer?: string | null;
  liaParecerEditado?: boolean;
  recommendation?: 'approve' | 'reject' | 'pending' | null;
  nextStage?: string | null;
  feedbackSent?: boolean;
  feedbackScheduledFor?: string | null;
  status?: 'draft' | 'completed';
  wsiScore?: WSIScore;
}

/**
 * Request para gerar perguntas com LIA
 */
export interface GenerateQuestionsRequest {
  jobId: string;
  candidateId: string;
  includeVagaQuestions: boolean;
  includeGapQuestions: boolean;
  includeFitCultural: boolean;
  wsiLevel?: string;
}

/**
 * Request para gerar parecer da entrevista
 * Alinhado com backend QuestionWithAnswer model
 */
export interface GenerateParecerRequest {
  interviewNoteId: string;
  candidateId?: string;
  jobId?: string;
  questions: Array<{
    id?: string;
    questionId?: string;
    text?: string;
    questionText?: string;
    starRating?: number | null;
    rating?: number | null;
    likertRating?: string | null;
    notes?: string;
    answer?: string;
    skipped?: boolean;
    category?: string;
    source?: string;
    blockType?: QuestionBlockType;
    skillId?: string;
    skillName?: string;
  }>;
  generalNotes?: string;
  transcription?: string | null;
}

/**
 * Pesos dos blocos WSI
 * Total: 1.0 (100%)
 * - Technical: 0.50 (50%)
 * - Behavioral: 0.20 (20%)
 * - Gap Analysis: 0.15 (15%)
 * - Contextual: 0.15 (15%)
 */
export const BLOCK_WEIGHTS: Record<QuestionBlockType, number> = {
  technical: 0.50,
  behavioral: 0.20,
  gap_analysis: 0.15,
  contextual: 0.15,
};

/**
 * Limiares de decisão para WSI agregado a partir de notas STAR de entrevista
 * presencial (componente `<ScoreCardWSI />` em interview-notes).
 *
 * IMPORTANTE — escopo distinto do WSI engine de screening:
 *   - Aqui: starRating 1-5 do recrutador → média ponderada → max 5.
 *   - Em `lib/wsi/visual.ts`: scorer determinístico do screening, escala 0-10.
 *
 * Não migrar para 0-10 sem antes mapear `starRating` para a nova escala. Ver
 * Task #512 (PR3 do #497) para histórico.
 */
export const WSI_THRESHOLDS = {
  approved: 4.2,
  humanReview: 3.8,
};

/**
 * Interview Analysis Status - Status da análise de entrevista Teams/Meet
 */
export interface InterviewAnalysisStatus {
  interview_id: string;
  status: 'awaiting_transcript' | 'transcript_ready' | 'analyzed' | 'scheduled' | 'completed';
  has_transcript: boolean;
  has_analysis: boolean;
  analysis_result?: InterviewAnalysisResult;
  error?: string;
}

/**
 * Interview Analysis Result - Resultado da análise de entrevista
 */
export interface InterviewAnalysisResult {
  overall_wsi_score: number;
  recommendation: 'approve' | 'reject' | 'pending_review';
  bloom_scores: Record<string, number>;
  dreyfus_scores: Record<string, number>;
  big_five_profile: Record<string, number>;
  star_completeness: number;
  key_insights: string[];
  concerns: string[];
}

// Re-export API types for consistency
export type {
  GenerateInterviewQuestionsRequest,
  GenerateInterviewQuestionsResponse,
  GenerateInterviewParecerRequest,
  GenerateInterviewParecerResponse,
} from '@/services/lia-api'
