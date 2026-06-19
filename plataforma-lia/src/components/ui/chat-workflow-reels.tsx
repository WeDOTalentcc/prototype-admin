"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  getCanonicalStage,
  CANONICAL_FUNNEL_STAGES,
  CANONICAL_UTILITY_STAGES,
  type CanonicalStage,
  type CanonicalStageId,
  type CanonicalUtilityId,
  type CanonicalStageColor,
} from "@/lib/canonical-funnel-stages";
import { useTranslations } from "next-intl";
import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
  useMemo,
} from "react";

export interface WorkflowReelSuggestion {
  id: string;
  title: string;
  description: string;
  command: string;
  /** PR-A: hint de domínio para routing determinístico no orchestrator. */
  domain_hint?: string;
  /** PR-A: hint de action/intent dentro do domínio. */
  intent_hint?: string;
  /** PR-K: quando definido, navega diretamente (sem detour pelo chat). */
  navigate_url?: string;
  /** PR-Q1: quando definido, abre modal via lia:open_modal (sem detour pelo chat). */
  modal_id?: string;
}

/**
 * PR-A — metadata enviada ao chat quando o usuário clica num card do Rail A.
 *
 * Consumida pelo `main_orchestrator.py` (`_prefer_hints_before_keyword_match`)
 * como guide computacional (per harness-engineering): rota determinística
 * antes do fallback keyword-based. Resolve FE-H03 do audit enterprise.
 */
export interface ChatSuggestionMetadata {
  source: "rail_a";
  card_id: string;
  stage: string;
  domain_hint?: string;
  intent_hint?: string;
}

/**
 * Mapa card_id → { domain_hint, intent_hint }. Fonte única de roteamento.
 *
 * Cada entrada foi validada contra `app/domains/<domain>/config/capabilities.yaml`
 * em 2026-04-26. Atualizar aqui quando novos cards forem adicionados ao Rail A
 * ou quando capabilities mudarem.
 *
 * Card 6.1 (register-hire) usa register_hire action (PR-C).

 */
export const SUGGESTION_HINTS: Record<
  string,
  { domain_hint?: string; intent_hint?: string }
> = {
  // Funil (13)
  "create-job": { domain_hint: "job_management", intent_hint: "create_job" },
  "job-template": {
    domain_hint: "job_management",
    intent_hint: "create_from_template",
  },
  "search-candidates": {
    domain_hint: "sourcing",
    intent_hint: "search_candidates",
  },
  "add-candidate": { domain_hint: "sourcing", intent_hint: "add_candidate" },
  "talent-pool": {
    domain_hint: "talent_pool",
    intent_hint: "list_talent_pools",
  },
  "candidate-info": {
    domain_hint: "recruiter_assistant",
    intent_hint: "quick_question",
  },
  "update-status": { domain_hint: "pipeline", intent_hint: "move_candidate" },
  "schedule-interview": {
    domain_hint: "interview_scheduling",
    intent_hint: "schedule_interview",
  },
  "reschedule-interview": {
    domain_hint: "interview_scheduling",
    intent_hint: "reschedule_interview",
  },
  "send-offer": { domain_hint: "offer", intent_hint: "send_offer" },
  "compare-candidates": {
    domain_hint: "sourcing",
    intent_hint: "compare_candidates",
  },
  "register-hire": { domain_hint: "pipeline", intent_hint: "register_hire" },
  "close-vacancy": { domain_hint: "job_management", intent_hint: "close_job" },
  // Utilitárias (9)
  "job-report": {
    domain_hint: "analytics",
    intent_hint: "generate_job_report",
  },
  "daily-briefing": {
    domain_hint: "recruiter_assistant",
    intent_hint: "daily_briefing",
  },
  "hiring-predictions": { domain_hint: "analytics", intent_hint: "forecast" },
  "configure-automations": {
    domain_hint: "automation",
    intent_hint: "create_automation",
  },
  "wsi-screening": {
    domain_hint: "interview_scheduling",
    intent_hint: "start_wsi_interview",
  },
  "ai-suggestions": {
    domain_hint: "recruiter_assistant",
    intent_hint: "suggest_action",
  },
  "ai-credits": {
    domain_hint: "agent_studio",
    intent_hint: "get_studio_consumption",
  },
  "hiring-policy": {
    domain_hint: "hiring_policy",
    intent_hint: "configure_policy",
  },
  "email-templates": {
    domain_hint: "communication",
    intent_hint: "create_template",
  },
};

/**
 * PR-K / PR-Q1: Cards que navegam diretamente para a página de destino
 * em vez de passar pelo chat. Evita o detour conversacional para ações
 * que têm páginas dedicadas.
 */
export const NAVIGATION_OVERRIDES: Record<string, string> = {
  /** Créditos IA = Consumo: deep-link direto para a seção consumo (redirect /ai-credits mantido p/ bookmarks legados). */
  "ai-credits": "/configuracoes?section=consumo",
  "hiring-policy": "/configuracoes?section=lia-personalizacao",  // V4: Politicas virou aba Regras do hub Comportamento da LIA
  "email-templates": "/configuracoes?section=templates-assinatura",
  /** PR-Q1: Banco de talentos tem página dedicada. */
  "talent-pool": "/bancos-de-talentos",
};

/**
 * Guide computacional: cards em estado "Em breve" (sem página nem modal).
 * Remover entrada quando a feature for implementada.
 * Single source of truth para coming-soon state no Rail A.
 * W1-3: VAZIO — ai-credits movido para NAVIGATION_OVERRIDES.
 */
export const COMING_SOON_CARDS = new Set<string>([]);

/**
 * PR-Q1 / W1-3: Cards que abrem modal diretamente (sem detour pelo chat).
 * Valor = modal_id reconhecido por LIAGlobalModals via lia:open_modal event.
 * create-job → CreateJobModal (escolhe "Criar em conversa" ou manual).
 * job-template NÃO entra aqui: vai direto pra conversa (command
 * "Criar vaga a partir de template" → orchestrator create_from_template),
 * pois criar-a-partir-de-modelo não tem caminho manual.
 */
export const MODAL_OVERRIDES: Record<string, string> = {
  "add-candidate": "add_candidate",
  /** Criar vaga abre CreateJobModal (step choose → conversa ou manual). */
  "create-job": "create_job",
};

export function buildSuggestionMetadata(
  cardId: string,
  stageId: string,
): ChatSuggestionMetadata {
  const hint = SUGGESTION_HINTS[cardId];
  return {
    source: "rail_a",
    card_id: cardId,
    stage: stageId,
    ...(hint?.domain_hint ? { domain_hint: hint.domain_hint } : {}),
    ...(hint?.intent_hint ? { intent_hint: hint.intent_hint } : {}),
  };
}

export interface WorkflowReelStage {
  id: string;
  label: string;
  shortLabel: string;
  icon: React.ElementType;
  pulseStageId?: string;
  color: CanonicalStageColor;
  suggestions: WorkflowReelSuggestion[];
}

interface PipelinePulseData {
  stages: Array<{ macro_stage: string; count: number }>;
  total: number;
  /** PR-M: active job vacancies count for the Vaga node pulse badge. */
  active_jobs?: number;
}

function usePipelinePulse() {
  const [pulse, setPulse] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/backend-proxy/pipeline-pulse")
      .then((res) => (res.ok ? res.json() : null))
      .then((data: PipelinePulseData | null) => {
        if (cancelled || !data) return;
        // Task #817 (canonical-fix, defesa em profundidade): mesmo com o
        // backend declarando `PipelinePulseResponse{stages, total}` via
        // Pydantic, o proxy pode retornar 200 OK com payload divergente em
        // cenários transitórios (cache stale, HMR em dev, response 200 com
        // body vazio quando o backend reinicia). Defensivo: tratar
        // `stages` ausente/não-array como "sem dados", não como crash.
        const stages = Array.isArray(data?.stages) ? data.stages : [];
        const map: Record<string, number> = {};
        for (const s of stages) {
          if (
            s &&
            typeof s.macro_stage === "string" &&
            typeof s.count === "number"
          ) {
            map[s.macro_stage] = s.count;
          }
        }
        // PR-M: wire active_jobs count for the Vaga node pulse badge.
        if (typeof data.active_jobs === "number" && data.active_jobs > 0) {
          map["definir-vaga"] = data.active_jobs;
        }
        setPulse(map);
      })
      .catch((err) => {
        console.warn("[chatWorkflowReels] pulse fetch failed", err);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { pulse, loading };
}

/**
 * PR-H: Rail A-specific concern — which suggestion cards belong to each stage.
 *
 * Stage ordering + icon + color come 100% from `canonicalFunnelStages.ts`.
 * This map only declares what is Rail-A-specific: card IDs per stage.
 * TypeScript enforces that every key must be a valid CanonicalStageId/UtilityId.
 */
const RAIL_A_SUGGESTIONS: Partial<
  Record<CanonicalStageId | CanonicalUtilityId, string[]>
> = {
  "definir-vaga":  ["create-job", "job-template"],
  "sourcing":      ["search-candidates", "add-candidate", "talent-pool"],
  "triagem":       ["candidate-info", "update-status"],
  "entrevista":    ["schedule-interview", "reschedule-interview"],
  "oferta":        ["send-offer", "compare-candidates"],
  "contratacao":   ["register-hire", "close-vacancy"],
  "analytics":     ["job-report", "daily-briefing", "hiring-predictions"],
  "ia-automacoes": ["configure-automations", "wsi-screening", "ai-suggestions"],
  "configuracoes": ["ai-credits", "hiring-policy", "email-templates"],
};

/**
 * PR-H: Build WorkflowReelStage[] from canonical stage definitions.
 *
 * Icon + color + ordering come from canonicalFunnelStages (single source of
 * truth). Rail-A-specific concerns (which cards, pulse badge) are layered on
 * top via RAIL_A_SUGGESTIONS and the withPulse flag.
 */
function useTranslatedStages(
  canonicalStages: CanonicalStage[],
  withPulse: boolean,
): WorkflowReelStage[] {
  const ts = useTranslations("chat.workflowReels.stages");
  const tsg = useTranslations("chat.workflowReels.suggestions");
  return useMemo(
    () =>
      canonicalStages.map((canonical) => {
        const suggestionIds =
          RAIL_A_SUGGESTIONS[canonical.key as CanonicalStageId | CanonicalUtilityId] ?? [];
        return {
          id: canonical.key,
          label: ts(`${canonical.key}.label` as `definir-vaga.label`),
          shortLabel: ts(`${canonical.key}.shortLabel` as `definir-vaga.shortLabel`),
          icon: canonical.Icon,
          pulseStageId: withPulse ? canonical.key : undefined,
          color: canonical.color,
          suggestions: suggestionIds.map((sid) => {
            const hint = SUGGESTION_HINTS[sid];
            return {
              id: sid,
              title: tsg(`${sid}.title` as `create-job.title`),
              description: tsg(`${sid}.description` as `create-job.description`),
              command: tsg(`${sid}.command` as `create-job.command`),
              domain_hint: hint?.domain_hint,
              intent_hint: hint?.intent_hint,
              navigate_url: NAVIGATION_OVERRIDES[sid],
              modal_id: MODAL_OVERRIDES[sid],
            };
          }),
        };
      }),
    // canonicalStages is a module-level constant — stable reference, not a dep.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [ts, tsg],
  );
}

interface ChatWorkflowReelsProps {
  /**
   * Callback disparado ao clicar num card. PR-A: além do `command` em PT-BR,
   * recebe `metadata` com hints de routing para o orchestrator.
   */
  onSelect: (command: string, metadata?: ChatSuggestionMetadata) => void;
  compact?: boolean;
  stages?: WorkflowReelStage[];
  utilityNodes?: WorkflowReelStage[];
}

const DOCK_MAX_SCALE = 1.4;
const DOCK_NEIGHBOR_1_SCALE = 1.2;
const DOCK_NEIGHBOR_2_SCALE = 1.1;
const DOCK_INFLUENCE_RADIUS = 120;
const DRAG_THRESHOLD = 5;

/** Delay em ms antes de expandir cards ao manter o mouse sobre um nó. */
const HOVER_INTENT_DELAY = 500;

function useDockMagnifier(
  containerRef: React.RefObject<HTMLDivElement | null>,
) {
  const mouseXRef = useRef<number | null>(null);
  const [mouseX, setMouseX] = useState<number | null>(null);
  const rafId = useRef<number>(0);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) =>
      setPrefersReducedMotion(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (prefersReducedMotion) return;
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const x = e.clientX - rect.left + (containerRef.current?.scrollLeft ?? 0);
      mouseXRef.current = x;
      if (!rafId.current) {
        rafId.current = requestAnimationFrame(() => {
          setMouseX(mouseXRef.current);
          rafId.current = 0;
        });
      }
    },
    [containerRef, prefersReducedMotion],
  );

  const handleMouseLeave = useCallback(() => {
    mouseXRef.current = null;
    if (rafId.current) {
      cancelAnimationFrame(rafId.current);
      rafId.current = 0;
    }
    setMouseX(null);
  }, []);

  const getScale = useCallback(
    (nodeIndex: number, nodeRefs: React.RefObject<(HTMLElement | null)[]>) => {
      if (mouseX === null || prefersReducedMotion) return 1;
      const nodeEl = nodeRefs.current?.[nodeIndex];
      if (!nodeEl) return 1;
      const nodeCenter = nodeEl.offsetLeft + nodeEl.offsetWidth / 2;
      const distance = Math.abs(mouseX - nodeCenter);
      if (distance > DOCK_INFLUENCE_RADIUS) return 1;

      const ratio = 1 - distance / DOCK_INFLUENCE_RADIUS;
      const eased = Math.cos(((1 - ratio) * Math.PI) / 2);

      if (distance < DOCK_INFLUENCE_RADIUS * 0.33) {
        return 1 + (DOCK_MAX_SCALE - 1) * eased;
      } else if (distance < DOCK_INFLUENCE_RADIUS * 0.66) {
        return 1 + (DOCK_NEIGHBOR_1_SCALE - 1) * eased;
      } else {
        return 1 + (DOCK_NEIGHBOR_2_SCALE - 1) * eased;
      }
    },
    [mouseX, prefersReducedMotion],
  );

  return {
    handleMouseMove,
    handleMouseLeave,
    getScale,
    isActive: mouseX !== null,
  };
}

function useDragToScroll(scrollRef: React.RefObject<HTMLDivElement | null>) {
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startScroll = useRef(0);
  const dragDistance = useRef(0);
  const [grabbing, setGrabbing] = useState(false);

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      const el = scrollRef.current;
      if (!el) return;
      isDragging.current = true;
      dragDistance.current = 0;
      startX.current = e.clientX;
      startScroll.current = el.scrollLeft;
    },
    [scrollRef],
  );

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return;
      const el = scrollRef.current;
      if (!el) return;
      const dx = e.clientX - startX.current;
      dragDistance.current = Math.abs(dx);
      if (dragDistance.current > DRAG_THRESHOLD) {
        setGrabbing(true);
        e.preventDefault();
        el.scrollLeft = startScroll.current - dx;
      }
    };

    const onMouseUp = () => {
      isDragging.current = false;
      setGrabbing(false);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [scrollRef]);

  const wasDragging = useCallback(() => {
    return dragDistance.current > DRAG_THRESHOLD;
  }, []);

  return { onMouseDown, grabbing, wasDragging };
}

/**
 * Hover intent: hover rápido → só magnifica (via useDockMagnifier).
 * Hover mantido por HOVER_INTENT_DELAY ms → expande cards do nó.
 * Após o primeiro unlock (cards abriram), troca de nó é imediata
 * enquanto o cursor permanecer dentro da área do reel.
 * Ao sair do reel, reseta o lock (próxima entrada exige delay novamente).
 */
function useHoverIntent() {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sessionActiveRef = useRef(false);

  const handleNodeEnter = useCallback((cb: () => void) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (sessionActiveRef.current) {
      cb();
    } else {
      timerRef.current = setTimeout(() => {
        sessionActiveRef.current = true;
        cb();
      }, HOVER_INTENT_DELAY);
    }
  }, []);

  const handleNodeLeave = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const handleReelLeave = useCallback((onClose: () => void) => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    sessionActiveRef.current = false;
    onClose();
  }, []);

  return { handleNodeEnter, handleNodeLeave, handleReelLeave };
}

export function ChatWorkflowReels({
  onSelect,
  compact = false,
  stages: stagesProp,
  utilityNodes: utilityNodesProp,
}: ChatWorkflowReelsProps) {
  const router = useRouter();
  const t = useTranslations("chat.workflowReels");
  const defaultStages = useTranslatedStages(CANONICAL_FUNNEL_STAGES, true);
  const defaultUtility = useTranslatedStages(CANONICAL_UTILITY_STAGES, false);
  const stages = stagesProp ?? defaultStages;
  const utilityNodes = utilityNodesProp ?? defaultUtility;
  const translatedStages = stages;
  const translatedUtility = utilityNodes;
  const allNodes = [...translatedStages, ...translatedUtility];
  const nodesWithSuggestions = allNodes.filter((s) => s.suggestions.length > 0);
  const firstWithSuggestions = nodesWithSuggestions[0]?.id ?? null;

  const { pulse } = usePipelinePulse();
  const [activeStageId, setActiveStageId] = useState<string | null>(
    firstWithSuggestions,
  );
  const scrollRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<(HTMLElement | null)[]>([]);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const activeStage = allNodes.find((s) => s.id === activeStageId) ?? null;

  const { handleMouseMove, handleMouseLeave, getScale } =
    useDockMagnifier(scrollRef);
  const { onMouseDown, grabbing, wasDragging } = useDragToScroll(scrollRef);
  const { handleNodeEnter, handleNodeLeave, handleReelLeave } = useHoverIntent();

  const handleNodeClick = (nodeId: string, hasSuggestions: boolean) => {
    if (wasDragging()) return;
    if (!hasSuggestions) return;
    setActiveStageId(activeStageId === nodeId ? null : nodeId);
  };

  const updateScrollState = () => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 4);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
  };

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    updateScrollState();
    el.addEventListener("scroll", updateScrollState, { passive: true });
    const ro = new ResizeObserver(updateScrollState);
    ro.observe(el);
    return () => {
      el.removeEventListener("scroll", updateScrollState);
      ro.disconnect();
    };
  }, []);

  const scroll = (dir: "left" | "right") => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollBy({ left: dir === "left" ? -160 : 160, behavior: "smooth" });
  };

  const setNodeRef = useCallback(
    (index: number) => (el: HTMLElement | null) => {
      nodeRefs.current[index] = el;
    },
    [],
  );

  if (compact) {
    return (
      <CompactReels
        stages={translatedStages}
        utilityNodes={translatedUtility}
        onSelect={onSelect}
      />
    );
  }

  let nodeIndex = 0;

  return (
    <div
      className="w-full space-y-5"
      onMouseLeave={() => handleReelLeave(() => setActiveStageId(null))}
    >
      <div className="relative" style={{ overflow: "visible" }}>
        {canScrollLeft && (
              <button
                onClick={() => scroll("left")}
                className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 z-10 w-6 h-6 rounded-full flex items-center justify-center bg-lia-bg-primary/80 border border-lia-border-subtle shadow-sm hover:bg-lia-bg-tertiary transition-colors opacity-60 hover:opacity-100"
                aria-label={t("scrollLeft")}
              >
                <ChevronLeft className="w-3.5 h-3.5 text-lia-text-secondary" />
              </button>
            )}
            {canScrollRight && (
              <button
                onClick={() => scroll("right")}
                className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1 z-10 w-6 h-6 rounded-full flex items-center justify-center bg-lia-bg-primary/80 border border-lia-border-subtle shadow-sm hover:bg-lia-bg-tertiary transition-colors opacity-60 hover:opacity-100"
                aria-label={t("scrollRight")}
              >
                <ChevronRight className="w-3.5 h-3.5 text-lia-text-secondary" />
              </button>
            )}

            <div
              ref={scrollRef}
              className="overflow-x-auto scrollbar-none"
              style={{
                scrollbarWidth: "none",
                msOverflowStyle: "none",
                cursor: grabbing ? "grabbing" : "grab",
                clipPath: "inset(-30px 0 0 0)",
              }}
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
              onMouseDown={onMouseDown}
            >
              <div className="flex items-end gap-0 min-w-max px-1 pt-8 pb-2">
                {translatedStages.map((stage, idx) => {
                  const currentIndex = nodeIndex++;
                  return (
                    <React.Fragment key={stage.id}>
                      <StageNode
                        ref={setNodeRef(currentIndex)}
                        stage={stage}
                        isActive={activeStageId === stage.id}
                        pulseCount={
                          stage.pulseStageId ? pulse[stage.pulseStageId] : undefined
                        }
                        onClick={() =>
                          handleNodeClick(stage.id, stage.suggestions.length > 0)
                        }
                        onMouseEnter={() => {
                          if (stage.suggestions.length > 0) {
                            handleNodeEnter(() => setActiveStageId(stage.id));
                          }
                        }}
                        onMouseLeave={handleNodeLeave}
                        scale={getScale(currentIndex, nodeRefs)}
                      />
                      {idx < translatedStages.length - 1 && (
                        <div
                          className="h-px w-6 flex-shrink-0 transition-colors self-center"
                          style={{
                            backgroundColor:
                              stage.suggestions.length > 0 &&
                              translatedStages[idx + 1].suggestions.length > 0
                                ? "var(--lia-border-default)"
                                : "var(--lia-border-subtle)",
                          }}
                        />
                      )}
                    </React.Fragment>
                  );
                })}

                {translatedUtility.length > 0 && (
                  <>
                    <div className="flex-shrink-0 w-px h-8 mx-3 bg-lia-border-subtle self-center" />
                    {translatedUtility.map((node, idx) => {
                      const currentIndex = nodeIndex++;
                      return (
                        <React.Fragment key={node.id}>
                          <StageNode
                            ref={setNodeRef(currentIndex)}
                            stage={node}
                            isActive={activeStageId === node.id}
                            onClick={() =>
                              handleNodeClick(node.id, node.suggestions.length > 0)
                            }
                            onMouseEnter={() => {
                              if (node.suggestions.length > 0) {
                                handleNodeEnter(() => setActiveStageId(node.id));
                              }
                            }}
                            onMouseLeave={handleNodeLeave}
                            scale={getScale(currentIndex, nodeRefs)}
                          />
                          {idx < translatedUtility.length - 1 && (
                            <div className="w-3 flex-shrink-0" />
                          )}
                        </React.Fragment>
                      );
                    })}
                  </>
                )}
              </div>
            </div>
          </div>

          {activeStage && activeStage.suggestions.length > 0 && (
            <div className="animate-fade-in-up">
              <div className="flex flex-wrap gap-3">
                {activeStage.suggestions.map((suggestion) => (
                  <button
                    key={suggestion.id}
                    data-rail-a-card={suggestion.id}
                    data-rail-a-stage={activeStage.id}
                    onClick={() => {
                      // Guide computacional: coming-soon cards mostram toast e retornam sem ação.
                      if (COMING_SOON_CARDS.has(suggestion.id)) {
                        toast.info("Em breve", {
                          description: "Esta funcionalidade estará disponível em breve.",
                        });
                        return;
                      }
                      // PR-O: include domain_hint + intent_hint + timestamp for granular analytics.
                      const _hint = SUGGESTION_HINTS[suggestion.id]
                      window.dispatchEvent(new CustomEvent("lia:rail-a-card-click", {
                        detail: {
                          card_id: suggestion.id,
                          stage_id: activeStage.id,
                          navigate: !!suggestion.navigate_url,
                          modal: !!suggestion.modal_id,
                          domain_hint: _hint?.domain_hint,
                          intent_hint: _hint?.intent_hint,
                          ts: Date.now(),
                        },
                      }));
                      if (suggestion.navigate_url) {
                        router.push(suggestion.navigate_url);
                      } else if (suggestion.modal_id) {
                        window.dispatchEvent(new CustomEvent("lia:open_modal", {
                          detail: { modal_id: suggestion.modal_id, data: {} },
                        }));
                      } else {
                        onSelect(
                          suggestion.command,
                          buildSuggestionMetadata(suggestion.id, activeStage.id),
                        );
                      }
                    }}
                    className={cn(
                      "flex items-start gap-3 p-4 text-left rounded-xl bg-lia-bg-primary border transition-all duration-150 group flex-1 min-w-[180px]",
                      COMING_SOON_CARDS.has(suggestion.id)
                        ? "opacity-60 cursor-default"
                        : "hover:-translate-y-0.5",
                    )}
                    style={{
                      borderColor: activeStage.color.cardBorder,
                    }}
                    onMouseEnter={(e) => {
                      if (COMING_SOON_CARDS.has(suggestion.id)) return;
                      e.currentTarget.style.borderColor =
                        activeStage.color.nodeBorder;
                      e.currentTarget.style.backgroundColor =
                        activeStage.color.accentBg;
                    }}
                    onMouseLeave={(e) => {
                      if (COMING_SOON_CARDS.has(suggestion.id)) return;
                      e.currentTarget.style.borderColor =
                        activeStage.color.cardBorder;
                      e.currentTarget.style.backgroundColor =
                        "var(--lia-bg-primary)";
                    }}
                  >
                    <div
                      className="rounded-lg p-2 flex-shrink-0"
                      style={{
                        backgroundColor: activeStage.color.accentBg,
                        color: activeStage.color.accent,
                      }}
                    >
                      {React.createElement(activeStage.icon, {
                        className: "w-4 h-4",
                      })}
                    </div>
                    <div className="min-w-0">
                      <span className="text-[14px] font-semibold text-lia-text-primary block mb-0.5">
                        {suggestion.title}
                        {COMING_SOON_CARDS.has(suggestion.id) && (
                          <span className="ml-1.5 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle align-middle">
                            Em breve
                          </span>
                        )}
                      </span>
                      <span className="text-xs leading-snug text-lia-text-secondary block">
                        {suggestion.description}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
  );
}

const StageNode = React.forwardRef<
  HTMLButtonElement,
  {
    stage: WorkflowReelStage;
    isActive: boolean;
    pulseCount?: number;
    onClick: () => void;
    onMouseEnter?: () => void;
    onMouseLeave?: () => void;
    scale?: number;
  }
>(function StageNode({ stage, isActive, pulseCount, onClick, onMouseEnter, onMouseLeave, scale = 1 }, ref) {
  const t = useTranslations("chat");
  const Icon = stage.icon;
  const hasSuggestions = stage.suggestions.length > 0;
  const showPulse = pulseCount !== undefined && pulseCount > 0;

  const handlePulseClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    window.location.href = "/funil-de-talentos?tab=pipeline";
  };

  return (
    <button
      ref={ref}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      disabled={!hasSuggestions}
      data-rail-a-node={stage.id}
      className="flex flex-col items-center gap-1.5 group px-2 disabled:cursor-default origin-bottom motion-reduce:!transition-none"
      title={
        hasSuggestions
          ? t("suggestionCount", {
              label: stage.label,
              count: stage.suggestions.length,
            })
          : stage.label
      }
      style={{
        transform: scale !== 1 ? `scale(${scale})` : undefined,
        transition: "transform 0.15s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
        willChange: scale !== 1 ? "transform" : "auto",
      }}
    >
      <div
        className="w-10 h-10 rounded-full flex items-center justify-center transition-colors duration-150 border-2"
        style={{
          backgroundColor: isActive
            ? stage.color.accent
            : hasSuggestions
              ? stage.color.accentBg
              : "var(--lia-bg-tertiary)",
          borderColor: isActive
            ? stage.color.accent
            : hasSuggestions
              ? stage.color.nodeBorder
              : "var(--lia-border-subtle)",
          boxShadow: isActive ? `0 0 0 3px ${stage.color.accentBg}` : undefined,
        }}
      >
        <Icon
          className="w-4 h-4 transition-colors"
          style={{
            color: isActive
              ? "var(--lia-text-on-accent)"
              : hasSuggestions
                ? stage.color.accent
                : "var(--lia-text-disabled)",
          }}
        />
      </div>
      <span
        className="text-micro font-medium transition-colors whitespace-nowrap"
        style={{
          color: isActive
            ? stage.color.accent
            : hasSuggestions
              ? "var(--lia-text-primary)"
              : "var(--lia-text-disabled)",
        }}
      >
        {stage.shortLabel}
      </span>
      {showPulse ? (
        <span
          className="text-micro font-bold cursor-pointer rounded-full px-1.5 py-0.5"
          style={{
            backgroundColor: stage.color.accentBg,
            color: stage.color.accent,
          }}
          onClick={handlePulseClick}
          title={t("pulseBadge", { count: pulseCount })}
        >
          {pulseCount}
        </span>
      ) : hasSuggestions ? (
        <span
          className="w-1 h-1 rounded-full transition-colors"
          style={{
            backgroundColor: stage.color.accent,
            opacity: isActive ? 1 : 0.5,
          }}
        />
      ) : null}
    </button>
  );
});

function CompactReels({
  stages,
  utilityNodes,
  onSelect,
}: {
  stages: WorkflowReelStage[];
  utilityNodes: WorkflowReelStage[];
  onSelect: (command: string, metadata?: ChatSuggestionMetadata) => void;
}) {
  // canonical-fix: pulse deve viver no componente que o usa, não como
  // variável capturada de escopo externo (bug detectado em teste de compact mode).
  const { pulse } = usePipelinePulse();
  // PR-Q1: router necessário para navigate_url dispatch no modo compact.
  const router = useRouter();
  // FE-S06: dock magnifier — paridade com modo expandido.
  const containerRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<(HTMLElement | null)[]>([]);
  const { handleMouseMove, handleMouseLeave, getScale } = useDockMagnifier(containerRef);
  const { handleNodeEnter, handleNodeLeave, handleReelLeave } = useHoverIntent();
  const setNodeRef = (index: number) => (el: HTMLElement | null) => {
    nodeRefs.current[index] = el;
  };
  const allNodes = [...stages, ...utilityNodes];
  const nodesWithSuggestions = allNodes.filter((s) => s.suggestions.length > 0);
  const firstWithSuggestions = nodesWithSuggestions[0]?.id ?? null;
  const [activeStageId, setActiveStageId] = useState<string | null>(
    firstWithSuggestions,
  );
  const activeStage = allNodes.find((s) => s.id === activeStageId) ?? null;

  const handleNodeClick = (nodeId: string, hasSuggestions: boolean) => {
    if (!hasSuggestions) return;
    setActiveStageId(activeStageId === nodeId ? null : nodeId);
  };

  return (
    <div
        className="space-y-2"
        onMouseLeave={() => handleReelLeave(() => setActiveStageId(null))}
      >
          <div
            ref={containerRef}
            className="flex items-center gap-1 overflow-x-auto scrollbar-none py-1"
            style={{ scrollbarWidth: "none" }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
          >
            {stages.map((stage, idx) => (
              <React.Fragment key={stage.id}>
                <CompactNode
                  ref={setNodeRef(idx) as React.Ref<HTMLButtonElement>}
                  stage={stage}
                  isActive={activeStageId === stage.id}
                  onClick={() =>
                    handleNodeClick(stage.id, stage.suggestions.length > 0)
                  }
                  onMouseEnter={() => {
                    if (stage.suggestions.length > 0) {
                      handleNodeEnter(() => setActiveStageId(stage.id));
                    }
                  }}
                  onMouseLeave={handleNodeLeave}
                  pulseCount={stage.pulseStageId ? pulse[stage.pulseStageId] : undefined}
                  scale={getScale(idx, nodeRefs)}
                />
                {idx < stages.length - 1 && (
                  <div className="h-px w-4 flex-shrink-0 bg-lia-border-subtle" />
                )}
              </React.Fragment>
            ))}

            {utilityNodes.length > 0 && (
              <>
                <div className="flex-shrink-0 w-px h-5 mx-1.5 bg-lia-border-subtle" />
                {utilityNodes.map((node, idx) => (
                  <React.Fragment key={node.id}>
                    <CompactNode
                      ref={setNodeRef(stages.length + idx) as React.Ref<HTMLButtonElement>}
                      stage={node}
                      isActive={activeStageId === node.id}
                      onClick={() =>
                        handleNodeClick(node.id, node.suggestions.length > 0)
                      }
                      onMouseEnter={() => {
                        if (node.suggestions.length > 0) {
                          handleNodeEnter(() => setActiveStageId(node.id));
                        }
                      }}
                      onMouseLeave={handleNodeLeave}
                      pulseCount={node.pulseStageId ? pulse[node.pulseStageId] : undefined}
                      scale={getScale(stages.length + idx, nodeRefs)}
                    />
                    {idx < utilityNodes.length - 1 && (
                      <div className="w-1 flex-shrink-0" />
                    )}
                  </React.Fragment>
                ))}
              </>
            )}
          </div>

          {activeStage && activeStage.suggestions.length > 0 && (
            <div className="space-y-1 animate-fade-in-up mt-2">
              {activeStage.suggestions.map((suggestion) => (
                <button
                  key={suggestion.id}
                  data-rail-a-card={suggestion.id}
                  data-rail-a-stage={activeStage.id}
                  onClick={() => {
                    // Guide computacional: coming-soon cards mostram toast (parity com expanded mode).
                    if (COMING_SOON_CARDS.has(suggestion.id)) {
                      toast.info("Em breve", {
                        description: "Esta funcionalidade estará disponível em breve.",
                      });
                      return;
                    }
                    // PR-O: include domain_hint + intent_hint + timestamp for granular analytics.
                    const _hint = SUGGESTION_HINTS[suggestion.id]
                    window.dispatchEvent(new CustomEvent("lia:rail-a-card-click", {
                      detail: {
                        card_id: suggestion.id,
                        stage_id: activeStage.id,
                        navigate: !!suggestion.navigate_url,
                        modal: !!suggestion.modal_id,
                        domain_hint: _hint?.domain_hint,
                        intent_hint: _hint?.intent_hint,
                        ts: Date.now(),
                      },
                    }));
                    if (suggestion.navigate_url) {
                      router.push(suggestion.navigate_url);
                    } else if (suggestion.modal_id) {
                      window.dispatchEvent(new CustomEvent("lia:open_modal", {
                        detail: { modal_id: suggestion.modal_id, data: {} },
                      }));
                    } else {
                      onSelect(
                        suggestion.command,
                        buildSuggestionMetadata(suggestion.id, activeStage.id),
                      );
                    }
                  }}
                  className="w-full flex items-center gap-2.5 p-2.5 rounded-xl text-left border transition-colors"
                  style={{
                    borderColor: activeStage.color.cardBorder,
                    backgroundColor: "var(--lia-bg-primary)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor =
                      activeStage.color.accentBg;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--lia-bg-primary)";
                  }}
                >
                  <div
                    className="p-1.5 rounded-md flex-shrink-0"
                    style={{
                      backgroundColor: activeStage.color.accentBg,
                      color: activeStage.color.accent,
                    }}
                  >
                    {React.createElement(activeStage.icon, {
                      className: "w-3.5 h-3.5",
                    })}
                  </div>
                  <span className="text-base-ui font-medium text-lia-text-primary">
                    {suggestion.title}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
  );
}

const CompactNode = React.forwardRef<
  HTMLButtonElement,
  {
    stage: WorkflowReelStage;
    isActive: boolean;
    onClick: () => void;
    onMouseEnter?: () => void;
    onMouseLeave?: () => void;
    pulseCount?: number;
    /** Dock magnifier scale factor (1 = no magnification). */
    scale?: number;
  }
>(function CompactNode({ stage, isActive, onClick, onMouseEnter, onMouseLeave, pulseCount, scale = 1 }, ref) {
  const Icon = stage.icon;
  const hasSuggestions = stage.suggestions.length > 0;
  const showPulse = pulseCount !== undefined && pulseCount > 0;

  return (
    <button
      ref={ref}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      disabled={!hasSuggestions}
      className="flex-shrink-0 flex flex-col items-center gap-0.5 px-1 disabled:cursor-default origin-bottom motion-reduce:!transition-none"
      title={stage.label}
      style={{
        transform: scale !== 1 ? `scale(${scale})` : undefined,
        transition: "transform 0.15s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
      }}
    >
      <div className="relative">
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center border transition-colors"
          style={{
            backgroundColor: isActive
              ? stage.color.accent
              : hasSuggestions
                ? stage.color.accentBg
                : "var(--lia-bg-tertiary)",
            borderColor: isActive
              ? stage.color.accent
              : hasSuggestions
                ? stage.color.nodeBorder
                : "var(--lia-border-subtle)",
          }}
        >
          <Icon
            className="w-3 h-3"
            style={{
              color: isActive
                ? "var(--lia-text-on-accent)"
                : hasSuggestions
                  ? stage.color.accent
                  : "var(--lia-text-disabled)",
            }}
          />
        </div>
        {showPulse && (
          <span
            className="absolute -top-1 -right-1.5 min-w-[14px] h-3.5 text-[9px] font-bold rounded-full flex items-center justify-center px-0.5"
            style={{
              backgroundColor: stage.color.accent,
              color: "var(--lia-text-on-accent)",
            }}
          >
            {pulseCount! > 99 ? "99+" : pulseCount}
          </span>
        )}
      </div>
      <span
        className="text-micro font-medium whitespace-nowrap"
        style={{
          color: hasSuggestions
            ? "var(--lia-text-secondary)"
            : "var(--lia-text-disabled)",
        }}
      >
        {stage.shortLabel}
      </span>
    </button>
  );
});
