"use client"

import React, { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import {
  Search, CheckCircle, Loader2, AlertCircle,
  Database, Briefcase, Heart,
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { textStyles, cardStyles, buttonStyles } from "@/lib/design-tokens"
import { useIdealProfile } from "@/hooks/talent-pools/use-ideal-profile"

interface StrategyResult {
  strategy_id: string
  strategy_name: string
  count: number
  elapsed_ms: number
  error: string | null
}

interface MultiStrategyCandidate {
  id: string
  name: string
  current_title: string
  current_company: string
  avatar_url: string | null
  skills: string[]
  multi_strategy_score: number
  found_via: string
  found_via_strategies?: string[]
}

interface MultiStrategySearchResult {
  total_unique: number
  elapsed_ms: number
  strategy_results: StrategyResult[]
  candidates: MultiStrategyCandidate[]
}

const STRATEGY_CONFIG: Record<string, { icon: string; color: string }> = {
  direct: { icon: "🎯", color: "bg-blue-100 text-blue-800" },
  adjacent: { icon: "🔀", color: "bg-purple-100 text-purple-800" },
  silver: { icon: "🥈", color: "bg-gray-100 text-gray-800" },
  reengagement: { icon: "💚", color: "bg-green-100 text-green-800" },
}

interface SourcingTabProps {
  /**
   * Pool destino canonical. Captação manual marca candidatos com
   * `origin='search'`, complementar ao agente automático (origin='agent').
   */
  poolId: string
  /**
   * ID do arquétipo (ideal_profile) vinculado ao pool. Quando presente,
   * pré-popula os inputs (jobTitle, skills) — recrutador edita se quiser.
   * Defensive: pool sem arquétipo → inputs vazios.
   */
  idealProfileId?: string | null
  /**
   * Opcional. Quando wired, executa após o POST canonical bem-sucedido
   * — para refresh local da lista de candidatos do pool, por exemplo.
   */
  onAddToPool?: (ids: string[], poolId: string) => void
  onAddToJob?: (ids: string[], jobId: string) => void
  onAddToList?: (ids: string[]) => void
}

export default function SourcingTab({
  poolId,
  idealProfileId,
  onAddToPool,
  onAddToJob,
  onAddToList,
}: SourcingTabProps) {
  const t = useTranslations("agents.multiStrategy")
  const { data: idealProfile } = useIdealProfile(idealProfileId ?? null)

  const [jobTitle, setJobTitle] = useState("")
  const [skills, setSkills] = useState("")
  const [location, setLocation] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const [isAdding, setIsAdding] = useState(false)
  const [result, setResult] = useState<MultiStrategySearchResult | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [strategiesInProgress, setStrategiesInProgress] = useState<Set<string>>(new Set())
  // Track se usuário editou manualmente, para não sobrescrever quando o
  // ideal_profile async chegar/mudar.
  const [userTouchedInputs, setUserTouchedInputs] = useState(false)

  // Pre-fill inputs a partir do ideal_profile quando disponível.
  // Só sobrescreve enquanto o usuário não tocou manualmente.
  useEffect(() => {
    if (!idealProfile || userTouchedInputs) return
    const mandatorySkills = idealProfile.mandatory_skills ?? []
    const preferredSkills = idealProfile.preferred_skills ?? []
    const skillsArr = [...mandatorySkills, ...preferredSkills]
    setJobTitle(idealProfile.name ?? "")
    setSkills(skillsArr.join(", "))
    // location: ideal_profile não traz location canonical. Mantém vazio
    // (recrutador preenche se relevante para a busca).
  }, [idealProfile, userTouchedInputs])

  const markTouched = () => {
    if (!userTouchedInputs) setUserTouchedInputs(true)
  }

  const handleSearch = async () => {
    if (!jobTitle.trim()) return
    setIsSearching(true)
    setResult(null)
    setSelectedIds(new Set())
    setStrategiesInProgress(new Set(["direct", "adjacent", "silver", "reengagement"]))

    try {
      const res = await fetch("/api/backend-proxy/sourcing/multi-strategy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_title: jobTitle.trim(),
          required_skills: skills.split(",").map((s) => s.trim()).filter(Boolean),
          location: location.trim(),
          strategies: ["direct", "adjacent", "silver", "reengagement"],
          limit: 50,
        }),
      })
      if (!res.ok) {
        console.error("Multi-strategy search error:", res.status)
        setStrategiesInProgress(new Set())
        return
      }
      const data = await res.json()
      setResult(data)
      setStrategiesInProgress(new Set())
    } catch (err) {
      console.error("Multi-strategy search failed:", err)
      setStrategiesInProgress(new Set())
    } finally {
      setIsSearching(false)
    }
  }

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) { next.delete(id) } else { next.add(id) }
      return next
    })
  }

  /**
   * Adiciona candidatos selecionados ao pool canonical.
   *
   * REGRA: usa `origin='search'` (captação manual) — complementar a
   * `origin='agent'` (auto). Endpoint backend honra esse campo via
   * `AddCandidatesToPoolRequest.origin`.
   *
   * POST canonical: /api/backend-proxy/talent-pools/:id/candidates
   *  → backend: POST /api/v1/talent_pools/:id/add_candidates
   */
  const handleAddToPoolCanonical = async () => {
    if (selectedIds.size === 0 || !poolId) return
    setIsAdding(true)
    try {
      const ids = Array.from(selectedIds)
      const res = await fetch(`/api/backend-proxy/talent-pools/${poolId}/candidates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_ids: ids,
          origin: "search",
        }),
      })
      if (!res.ok) {
        console.error("Add candidates to pool failed:", res.status)
        return
      }
      setSelectedIds(new Set())
      if (onAddToPool) onAddToPool(ids, poolId)
    } catch (err) {
      console.error("Add to pool failed:", err)
    } finally {
      setIsAdding(false)
    }
  }

  const inputClasses = "border border-lia-border-subtle rounded-md px-3 py-2 text-sm bg-lia-bg-primary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20"

  return (
    <div className="space-y-6">
      <Card className={cardStyles.default}>
        <CardContent className="p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => { markTouched(); setJobTitle(e.target.value) }}
              placeholder={t("jobTitlePlaceholder")}
              className={`flex-1 ${inputClasses}`}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <input
              type="text"
              value={skills}
              onChange={(e) => { markTouched(); setSkills(e.target.value) }}
              placeholder={t("skillsPlaceholder")}
              className={`w-48 ${inputClasses}`}
            />
            <input
              type="text"
              value={location}
              onChange={(e) => { markTouched(); setLocation(e.target.value) }}
              placeholder={t("locationPlaceholder")}
              className={`w-36 ${inputClasses}`}
            />
            <Button
              className={buttonStyles.primary}
              onClick={handleSearch}
              disabled={isSearching || !jobTitle.trim()}
            >
              <Search className="w-4 h-4 mr-1" />
              {isSearching ? t("searching") : t("search")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {(isSearching || result) && (
        <div className="flex gap-3">
          {["direct", "adjacent", "silver", "reengagement"].map((sid) => {
            const cfg = STRATEGY_CONFIG[sid]
            const sr = result?.strategy_results?.find((r) => r.strategy_id === sid)
            const inProgress = strategiesInProgress.has(sid)

            return (
              <Card key={sid} className={`${cardStyles.flat} flex-1`}>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{cfg.icon}</span>
                    {inProgress ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-lia-text-tertiary" />
                    ) : sr?.error ? (
                      <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                    ) : sr ? (
                      <CheckCircle className="w-3.5 h-3.5 text-green-500" />
                    ) : null}
                  </div>
                  <p className={textStyles.caption}>{sr?.strategy_name || sid}</p>
                  {sr && !sr.error && (
                    <p className={textStyles.metricSmall}>{t("candidatesCount", { count: sr.count })}</p>
                  )}
                  {sr?.error && (
                    <p className="text-xs text-red-500">{t("error")}</p>
                  )}
                  {sr && (
                    <p className="text-[10px] text-lia-text-tertiary">{sr.elapsed_ms}ms</p>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {result && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={textStyles.subtitle}>
              {t("uniqueCandidatesFound", { count: result.total_unique })}
            </span>
            <span className={textStyles.caption}>
              {t("inMs", { ms: result.elapsed_ms })}
            </span>
          </div>
          {/* Sprint 4 v3: CTA primária canonical = "+ Banco" wired ao pool atual via
              POST /api/backend-proxy/talent-pools/:id/candidates com origin='search'.
              CTAs job/list permanecem opt-in (passadas como callback) — usadas
              em entry-points fora do TalentPoolPage caso necessário. */}
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-2">
              <span className={textStyles.caption}>{t("selected", { count: selectedIds.size })}</span>
              <Button
                className={buttonStyles.primary}
                onClick={handleAddToPoolCanonical}
                disabled={isAdding}
              >
                {isAdding ? (
                  <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                ) : (
                  <Database className="w-3.5 h-3.5 mr-1" />
                )}
                {`+ ${t("pool")}`}
              </Button>
              {onAddToJob && (
                <Button
                  className={buttonStyles.outline}
                  onClick={() => onAddToJob(Array.from(selectedIds), "")}
                >
                  <Briefcase className="w-3.5 h-3.5 mr-1" /> {`+ ${t("job")}`}
                </Button>
              )}
              {onAddToList && (
                <Button
                  className={buttonStyles.outline}
                  onClick={() => onAddToList(Array.from(selectedIds))}
                >
                  <Heart className="w-3.5 h-3.5 mr-1" /> {`+ ${t("list")}`}
                </Button>
              )}
            </div>
          )}
        </div>
      )}

      {result && result.candidates.length > 0 && (
        <div className="overflow-auto max-h-[500px]">
          <table className="w-full">
            <thead className="sticky top-0 bg-white">
              <tr className="border-b border-lia-border-subtle">
                <th className="py-2 px-3 text-left w-8">
                  <input
                    type="checkbox"
                    checked={selectedIds.size === result.candidates.length}
                    onChange={() => {
                      if (selectedIds.size === result.candidates.length) setSelectedIds(new Set())
                      else setSelectedIds(new Set(result.candidates.map((c) => c.id)))
                    }}
                    className="rounded border-lia-border-default"
                  />
                </th>
                <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}>{t("candidate")}</th>
                <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}>{t("score")}</th>
                <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}>{t("strategy")}</th>
                <th className={`py-2 px-3 text-left ${textStyles.labelSmall}`}>{t("skills")}</th>
              </tr>
            </thead>
            <tbody>
              {result.candidates.map((c) => {
                const strategies = c.found_via_strategies || [c.found_via]
                return (
                  <tr key={c.id} className="hover:bg-lia-bg-secondary">
                    <td className="py-2 px-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(c.id)}
                        onChange={() => toggleSelect(c.id)}
                        className="rounded border-lia-border-default"
                      />
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex items-center gap-2">
                        <Avatar className="w-7 h-7">
                          <AvatarImage src={c.avatar_url || undefined} alt={c.name || "Candidato"} />
                          <AvatarFallback>{c.name?.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className={`${textStyles.body} font-medium`}>{c.name}</p>
                          <p className={textStyles.caption}>
                            {[c.current_title, c.current_company].filter(Boolean).join(" ·")}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <span className={`${textStyles.subtitle} font-mono`}>
                        {c.multi_strategy_score}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {strategies.map((s) => {
                          const cfg = STRATEGY_CONFIG[s]
                          return cfg ? (
                            <Chip variant="neutral" muted key={s} className={`${cfg.color} text-xs`} title={s}>
                              {cfg.icon}
                            </Chip>
                          ) : null
                        })}
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {c.skills?.slice(0, 4).map((sk) => (
                          <Chip density="relaxed" variant="neutral" muted key={sk} className="bg-lia-bg-tertiary text-lia-text-secondary">{sk}</Chip>
                        ))}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
