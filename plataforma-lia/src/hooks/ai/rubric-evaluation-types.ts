/**
 * Re-export canonical pra evitar duplicação de tipos com
 * `src/components/rubric-evaluation-types.ts`.
 *
 * Histórico: este arquivo foi criado pra resolver TS2307 em
 * `use-rubric-evaluation.ts` (refactor moveu helpers pra hook). O conteúdo
 * canonical vive em `src/components/rubric-evaluation-types.ts` porque o
 * modal consome lá. Reusar evita TS2322 mismatch entre os dois.
 */
export type {
  RubricEvaluationData,
  RubricRequirement,
  RedFlag,
  ParecerLIA,
  DecisionBadge,
  ScoreBadge,
  RubricStyle,
  PriorityStyle,
} from "@/components/rubric-evaluation-types"
