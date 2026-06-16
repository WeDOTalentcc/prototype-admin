/**
 * Tour step definitions for the onboarding guided tour.
 *
 * Each step: LIA message in chat → visual action (spotlight/autofill/screenshot/navigate).
 * Steps are sequential. Tour ends when all steps complete or user skips.
 */

import type { TourStep } from "./TourController"

export const ONBOARDING_TOUR_STEPS: TourStep[] = [
  // --- Part 1: Platform overview ---
  {
    id: "welcome",
    type: "message_only",
    message: "Vou te mostrar como a plataforma esta organizada. Sao 4 areas principais:",
    autoAdvanceMs: 3000,
  },
  {
    id: "tour_pipeline",
    type: "spotlight",
    message: "1. PIPELINE — e seu centro de controle. Aqui voce ve TODAS as vagas, com cada candidato em cada etapa. Voce aprova, rejeita, move candidatos, e eu te ajudo em cada decisao.",
    selector: "[data-tour='nav-pipeline'], [data-nav='pipeline'], a[href*='pipeline']",
    spotlightText: "Funil — centro de controle de vagas e candidatos",
    position: "right",
  },
  {
    id: "tour_campaigns",
    type: "spotlight",
    message: "2. CAMPANHAS — cada vaga tem uma campanha de recrutamento com etapas automaticas: sourcing, triagem, entrevista, oferta.",
    selector: "[data-tour='nav-campaigns'], [data-nav='campaigns']",
    spotlightText: "Campanhas — fluxo automatico de recrutamento",
    position: "right",
  },
  {
    id: "tour_agent_studio",
    type: "spotlight",
    message: "3. AGENT STUDIO — aqui ficam os agentes de IA que trabalham para voce 24/7. Cada agente pode estar vinculado a uma VAGA, um BANCO VIVO (Talent Pool), ou uma LISTA. Voce configura uma vez, o agente trabalha sozinho.",
    selector: "[data-tour='nav-agent-studio'], [data-nav='agent-studio'], a[href*='agent']",
    spotlightText: "Agent Studio — agentes de IA autonomos",
    position: "right",
  },
  {
    id: "tour_lia",
    type: "spotlight",
    message: "4. EU — sua assistente de IA! Estou em TODAS as telas. Voce pode me chamar a qualquer momento pelo chat, por texto ou por AUDIO. E eu APRENDO com cada decisao sua.",
    selector: "[data-tour='chat-input'], [data-tour='lia-chat'], textarea",
    spotlightText: "Chat — sua assistente de IA",
    position: "top",
  },

  // --- Part 2: How it works day-to-day ---
  {
    id: "tour_daily",
    type: "message_only",
    message: "No dia-a-dia funciona assim:\n1. Voce abre uma vaga (eu ajudo a criar o JD e perguntas)\n2. Um agente busca candidatos automaticamente\n3. Candidatos sao triados por chat, ligacao ou WhatsApp\n4. Eu emito parecer detalhado com score e recomendacao\n5. Voce decide quem avanca no Funil\n6. Eu agendo entrevistas e acompanho ate a oferta\n\nTudo com transparencia — voce sempre ve o que eu fiz e por que.",
    autoAdvanceMs: 8000,
  },

  // --- Part 3: Action choice ---
  {
    id: "tour_action",
    type: "message_only",
    message: "Agora que voce conhece a plataforma, vamos colocar a mao na massa! Voce ja tem alguma vaga aberta que quer trabalhar?",
    autoAdvanceMs: 0, // Wait for user choice
  },
]

/**
 * Tour steps for the job creation demo (after user chooses "Criar vaga nova").
 * These wrap the Wizard WSI with extra didactic LIA messages.
 */
export const JOB_CREATION_DEMO_STEPS: TourStep[] = [
  {
    id: "demo_start",
    type: "message_only",
    message: "Descreva a vaga que quer criar. Pode ser simples — 'Dev Python Senior' — que eu cuido do resto.",
    autoAdvanceMs: 0,
  },
  {
    id: "demo_enrichment",
    type: "message_only",
    message: "Olha o que eu fiz! Enriqueci o JD, identifiquei competências, mapeei competencias e verifiquei linguagem inclusiva. Tudo automatico.",
    autoAdvanceMs: 5000,
  },
  {
    id: "demo_questions",
    type: "message_only",
    message: "Agora gerei perguntas de triagem calibradas por senioridade. Cada pergunta avalia competencia real com base em situacoes vividas (CBI), profundidade cognitiva (Bloom) e maturidade (Dreyfus). Voce pode editar qualquer uma.",
    autoAdvanceMs: 5000,
  },
  {
    id: "demo_publish",
    type: "message_only",
    message: "Pronto! Quando voce aprovar, eu publico e comeco a triar candidatos automaticamente. Quanto tempo isso levaria sem mim?",
    autoAdvanceMs: 0,
  },
]
