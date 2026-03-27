/**
 * Database schema for WSI (WeDoTalent Skill Index) methodology.
 * 
 * Stores:
 * - Competency suggestions
 * - WSI questions
 * - Response analyses
 * - WSI results
 * - Structured reports
 * - Candidate feedbacks
 */
import { pgTable, serial, varchar, text, timestamp, jsonb, real, integer, boolean } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';
import { candidates, jobVacancies } from './schema';

/**
 * Competency Suggestions
 * Stores automatic suggestions of competencies to evaluate based on JD.
 */
export const competencySuggestions = pgTable('competency_suggestions', {
  id: serial('id').primaryKey(),
  jobVacancyId: varchar('job_vacancy_id').notNull().references(() => jobVacancies.id),
  
  technicalCompetencies: jsonb('technical_competencies').notNull(), // Array of Competency objects
  behavioralCompetencies: jsonb('behavioral_competencies').notNull(),
  culturalCompetencies: jsonb('cultural_competencies').notNull(),
  
  suggestedWeights: jsonb('suggested_weights').notNull(), // {competency: weight}
  confidenceScore: real('confidence_score').notNull(),
  
  status: varchar('status').notNull().default('pending'), // pending, approved, rejected
  reviewedBy: varchar('reviewed_by'),
  reviewNotes: text('review_notes'),
  
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

/**
 * WSI Questions
 * Stores generated questions for screening based on methodology.
 */
export const wsiQuestions = pgTable('wsi_questions', {
  id: serial('id').primaryKey(),
  jobVacancyId: varchar('job_vacancy_id').notNull().references(() => jobVacancies.id),
  competencySuggestionId: integer('competency_suggestion_id').references(() => competencySuggestions.id),
  
  competency: varchar('competency').notNull(),
  framework: varchar('framework').notNull(), // CBI, Bloom, Dreyfus, BigFive
  questionType: varchar('question_type').notNull(), // autodeclaration, contextual, microcase, situational
  questionText: text('question_text').notNull(),
  
  weight: real('weight').notNull(),
  expectedSignals: jsonb('expected_signals').notNull(), // Array of strings
  scoringCriteria: jsonb('scoring_criteria').notNull(), // {score_5: ..., score_3: ..., score_1: ...}
  
  isActive: boolean('is_active').notNull().default(true),
  
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

/**
 * Response Analyses
 * Stores analysis of each candidate response with scores.
 */
export const responseAnalyses = pgTable('response_analyses', {
  id: serial('id').primaryKey(),
  candidateId: varchar('candidate_id').notNull().references(() => candidates.id),
  questionId: integer('question_id').notNull().references(() => wsiQuestions.id),
  
  competency: varchar('competency').notNull(),
  responseText: text('response_text').notNull(),
  
  // Scores
  autodeclarationScore: real('autodeclaration_score'), // 1-5
  contextScore: real('context_score'), // 1-5
  bloomLevel: integer('bloom_level'), // 1-5
  dreyfusLevel: integer('dreyfus_level'), // 1-5
  
  // Analysis
  evidences: jsonb('evidences').notNull(), // Array of strings
  redFlags: jsonb('red_flags').notNull(), // Array of strings
  consistencyPenalty: real('consistency_penalty').notNull().default(0),
  
  finalScore: real('final_score').notNull(), // 1-5
  justification: text('justification').notNull(),
  
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

/**
 * WSI Results
 * Stores final WSI score and classification for each candidate.
 */
export const wsiResults = pgTable('wsi_results', {
  id: serial('id').primaryKey(),
  candidateId: varchar('candidate_id').notNull().references(() => candidates.id),
  jobVacancyId: varchar('job_vacancy_id').notNull().references(() => jobVacancies.id),
  
  // WSI Scores
  technicalWsi: real('technical_wsi').notNull(), // 0-5
  behavioralWsi: real('behavioral_wsi').notNull(), // 0-5
  overallWsi: real('overall_wsi').notNull(), // 0-5
  
  // Classification
  classification: varchar('classification').notNull(), // excelente, alto, medio, regular, baixo
  percentile: integer('percentile'), // 0-100
  
  // Ranking
  rankPosition: integer('rank_position'), // Position in ranking for this job vacancy
  totalCandidates: integer('total_candidates'), // Total candidates evaluated
  
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

/**
 * Structured Reports
 * Stores detailed reports for recruiters.
 */
export const structuredReports = pgTable('structured_reports', {
  id: serial('id').primaryKey(),
  candidateId: varchar('candidate_id').notNull().references(() => candidates.id),
  wsiResultId: integer('wsi_result_id').notNull().references(() => wsiResults.id),
  
  // Report sections
  executiveSummary: text('executive_summary').notNull(),
  
  technicalAnalysis: jsonb('technical_analysis').notNull(), // {pontos_fortes, gaps, evidencias}
  behavioralAnalysis: jsonb('behavioral_analysis').notNull(), // {colaboracao, inovacao, comunicacao}
  culturalFit: jsonb('cultural_fit').notNull(), // {score, valores_alinhados, atencao}
  
  recommendation: jsonb('recommendation').notNull(), // {decisao, justificativa, proximos_passos}
  
  viewedBy: varchar('viewed_by'),
  viewedAt: timestamp('viewed_at'),
  
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

/**
 * Candidate Feedbacks
 * Stores structured feedbacks sent to candidates.
 */
export const candidateFeedbacks = pgTable('candidate_feedbacks', {
  id: serial('id').primaryKey(),
  candidateId: varchar('candidate_id').notNull().references(() => candidates.id),
  wsiResultId: integer('wsi_result_id').notNull().references(() => wsiResults.id),
  
  decision: varchar('decision').notNull(), // aprovado, aguardando, nao_aprovado
  
  mainMessage: text('main_message').notNull(),
  technicalStrengths: jsonb('technical_strengths').notNull(), // Array of strings
  developmentOpportunities: jsonb('development_opportunities').notNull(),
  behavioralStrengths: jsonb('behavioral_strengths').notNull(),
  
  nextSteps: text('next_steps').notNull(),
  personalizedTip: text('personalized_tip'),
  developmentPlan: jsonb('development_plan'), // {curto_prazo: [], medio_prazo: []}
  recommendedResources: jsonb('recommended_resources'), // Array of strings
  
  sentAt: timestamp('sent_at'),
  deliveryStatus: varchar('delivery_status').default('pending'), // pending, sent, failed
  
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// Relations
export const competencySuggestionsRelations = relations(competencySuggestions, ({ one }) => ({
  jobVacancy: one(jobVacancies, {
    fields: [competencySuggestions.jobVacancyId],
    references: [jobVacancies.id],
  }),
}));

export const wsiQuestionsRelations = relations(wsiQuestions, ({ one }) => ({
  jobVacancy: one(jobVacancies, {
    fields: [wsiQuestions.jobVacancyId],
    references: [jobVacancies.id],
  }),
  competencySuggestion: one(competencySuggestions, {
    fields: [wsiQuestions.competencySuggestionId],
    references: [competencySuggestions.id],
  }),
}));

export const responseAnalysesRelations = relations(responseAnalyses, ({ one }) => ({
  candidate: one(candidates, {
    fields: [responseAnalyses.candidateId],
    references: [candidates.id],
  }),
  question: one(wsiQuestions, {
    fields: [responseAnalyses.questionId],
    references: [wsiQuestions.id],
  }),
}));

export const wsiResultsRelations = relations(wsiResults, ({ one }) => ({
  candidate: one(candidates, {
    fields: [wsiResults.candidateId],
    references: [candidates.id],
  }),
  jobVacancy: one(jobVacancies, {
    fields: [wsiResults.jobVacancyId],
    references: [jobVacancies.id],
  }),
}));

export const structuredReportsRelations = relations(structuredReports, ({ one }) => ({
  candidate: one(candidates, {
    fields: [structuredReports.candidateId],
    references: [candidates.id],
  }),
  wsiResult: one(wsiResults, {
    fields: [structuredReports.wsiResultId],
    references: [wsiResults.id],
  }),
}));

export const candidateFeedbacksRelations = relations(candidateFeedbacks, ({ one }) => ({
  candidate: one(candidates, {
    fields: [candidateFeedbacks.candidateId],
    references: [candidates.id],
  }),
  wsiResult: one(wsiResults, {
    fields: [candidateFeedbacks.wsiResultId],
    references: [wsiResults.id],
  }),
}));
