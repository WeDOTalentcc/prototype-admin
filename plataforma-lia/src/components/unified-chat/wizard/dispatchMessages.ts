/**
 * Dispatch messages canonical entre frontend wizard e backend graph.
 *
 * Pattern frágil identificado em audit F-4.11: frontend dispatch
 * sendChatMessage(literal_string) e backend parsea via regex em
 * pipeline_template_node. Mudança de copy em qualquer lado quebra
 * silenciosamente.
 *
 * Esta constante é canonical para AMBOS lados. Mirror em:
 *   lia-agent-system/app/domains/job_creation/dispatch_messages.py
 *
 * NÃO MUDAR sem atualizar dispatch_messages.py simultaneamente.
 *
 * Sensor schema-sync (futuro PR): comparar strings TS↔Python (decodificando
 * ambos como UTF-8 e validando equivalência semântica das regex).
 */

export const WIZARD_PIPELINE_TEMPLATE_DISPATCH = {
  /** Recrutador escolheu template via wizard (sem vaga persistida ainda). */
  applyTemplate: (templateId: string): string =>
    `Aplicar template de pipeline ${templateId}`,

  /** Recrutador já aplicou via fetch separado, avisa backend pra seguir. */
  appliedAck: "Template de pipeline aplicado, pode seguir.",

  /** Recrutador optou por usar pipeline padrão da empresa. */
  useDefault: "Usar pipeline padrão da empresa.",
} as const;
