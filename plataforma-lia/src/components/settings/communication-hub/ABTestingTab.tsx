"use client"

import { useState, useEffect, useCallback } from "react"
import { useTranslations } from "next-intl"
import { FlaskConical, Plus, BarChart3, Loader2, AlertCircle, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { InteractiveSurface } from "@/components/ui/interactive-surface"

interface ABVariant {
  variant_name: string
  traffic_percentage: number
  is_active?: boolean
}

interface ABTest {
  test_name: string
  variants: ABVariant[]
  created_at?: string | null
}

interface ABTestMetrics {
  test_name: string
  variants: Record<string, { metrics: Record<string, { sample_size: number; mean: number; std_dev: number; confidence_interval_95: number[] }> }>
  statistical_significance: Record<string, { control: string; variant: string; metric: string; z_score: number; p_value: number; improvement_pct: number; is_significant: boolean }> | null
  winner: { variant: string; metric: string; improvement_pct: number; p_value: number } | null
  total_observations: number
}

interface CreateTestForm {
  test_name: string
  variants: { variant_name: string; prompt_template: string; traffic_percentage: number }[]
}

const EMPTY_FORM: CreateTestForm = {
  test_name: "",
  variants: [
    { variant_name: "control", prompt_template: "", traffic_percentage: 50 },
    { variant_name: "treatment", prompt_template: "", traffic_percentage: 50 },
  ],
}

const AB_TESTS_URL = "/api/backend-proxy/ab-tests"

export function ABTestingTab() {
  const t = useTranslations("settings.communication.abtesting")
  const [tests, setTests] = useState<ABTest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedTest, setExpandedTest] = useState<string | null>(null)
  const [metricsMap, setMetricsMap] = useState<Record<string, ABTestMetrics>>({})
  const [metricsLoading, setMetricsLoading] = useState<Record<string, boolean>>({})
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [form, setForm] = useState<CreateTestForm>(EMPTY_FORM)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createSuccess, setCreateSuccess] = useState<string | null>(null)

  const fetchTests = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiFetch(AB_TESTS_URL)
      if (!response.ok) throw new Error(t("loadError", { status: response.statusText }))
      const data = await response.json()
      setTests(data.tests || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : t("loadErrorGeneric"))
    } finally {
      setLoading(false)
    }
  }, [t])

  const fetchMetrics = useCallback(async (testName: string) => {
    setMetricsLoading(prev => ({ ...prev, [testName]: true }))
    try {
      const response = await apiFetch(`${AB_TESTS_URL}/${encodeURIComponent(testName)}/results`)
      if (!response.ok) throw new Error(t("metricsError"))
      const data: ABTestMetrics = await response.json()
      setMetricsMap(prev => ({ ...prev, [testName]: data }))
    } catch {
      // Non-fatal - leave metrics empty
    } finally {
      setMetricsLoading(prev => ({ ...prev, [testName]: false }))
    }
  }, [t])

  useEffect(() => {
    fetchTests()
  }, [fetchTests])

  const toggleExpand = (testName: string) => {
    if (expandedTest === testName) {
      setExpandedTest(null)
    } else {
      setExpandedTest(testName)
      if (!metricsMap[testName]) {
        fetchMetrics(testName)
      }
    }
  }

  const handleFormVariantChange = (index: number, field: keyof CreateTestForm["variants"][0], value: string | number) => {
    setForm(prev => ({
      ...prev,
      variants: prev.variants.map((v, i) => i === index ? { ...v, [field]: value } : v),
    }))
  }

  const addVariant = () => {
    setForm(prev => ({
      ...prev,
      variants: [...prev.variants, { variant_name: `variant_${prev.variants.length}`, prompt_template: "", traffic_percentage: 0 }],
    }))
  }

  const removeVariant = (index: number) => {
    if (form.variants.length <= 2) return
    setForm(prev => ({ ...prev, variants: prev.variants.filter((_, i) => i !== index) }))
  }

  const handleCreate = async () => {
    setCreateError(null)
    setCreateSuccess(null)

    if (!form.test_name.trim()) {
      setCreateError(t("experimentNameRequired"))
      return
    }

    const totalTraffic = form.variants.reduce((sum, v) => sum + Number(v.traffic_percentage), 0)
    if (Math.abs(totalTraffic - 100) > 0.1) {
      setCreateError(t("trafficSumError", { total: totalTraffic }))
      return
    }

    setCreating(true)
    try {
      const response = await apiFetch(AB_TESTS_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          test_name: form.test_name.trim(),
          variants: form.variants,
        }),
      })

      const data = await response.json()
      if (!response.ok || data.error) {
        throw new Error(data.error || data.detail || t("createError"))
      }

      setCreateSuccess(t("experimentCreated", { name: form.test_name }))
      notifyChatOfSettingsUpdate({
        actionId: "create_ab_test",
        section: "communication",
        field: form.test_name,
        value: form.variants.length,
      })
      setForm(EMPTY_FORM)
      setShowCreateForm(false)
      fetchTests()
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : t("createError"))
    } finally {
      setCreating(false)
    }
  }

  const getStatusColor = (metrics: ABTestMetrics | undefined) => {
    if (!metrics) return "bg-lia-bg-secondary text-lia-text-tertiary"
    if (metrics.winner) return "bg-status-success/15 text-status-success"
    if (metrics.total_observations > 0) return "bg-wedo-cyan/10 text-wedo-cyan"
    return "bg-lia-bg-secondary text-lia-text-tertiary"
  }

  const getStatusLabel = (metrics: ABTestMetrics | undefined) => {
    if (!metrics) return t("noData")
    if (metrics.winner) return t("winnerIdentified")
    if (metrics.total_observations > 0) return t("inProgress")
    return t("awaitingData")
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-lia-text-primary flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-wedo-cyan" />
            {t("title")}
          </h3>
          <p className="text-xs text-lia-text-tertiary mt-0.5">
            {t("description")}
          </p>
        </div>
        <Button
          size="sm"
          onClick={() => { setShowCreateForm(!showCreateForm); setCreateError(null); setCreateSuccess(null) }}
          className="text-xs"
        >
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          {t("newExperiment")}
        </Button>
      </div>

      {createSuccess && (
        <div className="flex items-center gap-2 text-xs text-status-success bg-status-success/10 border border-status-success/30 rounded-md px-3 py-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          {createSuccess}
        </div>
      )}

      {showCreateForm && (
        <div className="border border-lia-border-subtle rounded-md p-4 bg-lia-bg-secondary space-y-4">
          <h4 className="text-sm font-semibold text-lia-text-primary">{t("newExperimentTitle")}</h4>

          <div>
            <label className="text-xs font-medium text-lia-text-secondary block mb-1">{t("experimentNameLabel")}</label>
            <Input
              type="text"
              value={form.test_name}
              onChange={e => setForm(prev => ({ ...prev, test_name: e.target.value }))}
              placeholder={t("experimentNamePlaceholder")}
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-lia-text-secondary">{t("variantsLabel")}</label>
              <Button
                variant="ghost"
                size="sm"
                onClick={addVariant}
                className="text-xs text-wedo-cyan hover:text-wedo-cyan-dark h-auto px-2 py-1"
              >
                {t("addVariantBtn")}
              </Button>
            </div>

            {form.variants.map((variant, i) => (
              <div key={i} className="border border-lia-border-subtle rounded-md p-3 space-y-2 bg-lia-bg-primary">
                <div className="flex items-center gap-2">
                  <div className="flex-1">
                    <label className="text-[10px] text-lia-text-tertiary block mb-0.5">{t("variantNameSmall")}</label>
                    <Input
                      type="text"
                      value={variant.variant_name}
                      onChange={e => handleFormVariantChange(i, "variant_name", e.target.value)}
                      className="h-8 text-xs"
                    />
                  </div>
                  <div className="w-24">
                    <label className="text-[10px] text-lia-text-tertiary block mb-0.5">{t("trafficSmall")}</label>
                    <Input
                      type="number"
                      min={0}
                      max={100}
                      value={variant.traffic_percentage}
                      onChange={e => handleFormVariantChange(i, "traffic_percentage", parseFloat(e.target.value) || 0)}
                      className="h-8 text-xs"
                    />
                  </div>
                  {form.variants.length > 2 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeVariant(i)}
                      className="text-status-error text-xs mt-4 hover:opacity-80 h-auto px-2 py-1"
                    >
                      ✕
                    </Button>
                  )}
                </div>
                <div>
                  <label className="text-[10px] text-lia-text-tertiary block mb-0.5">{t("templateLabel")}</label>
                  <Textarea
                    value={variant.prompt_template}
                    onChange={e => handleFormVariantChange(i, "prompt_template", e.target.value)}
                    placeholder={t("templatePlaceholder", { placeholder: "{{candidate_name}}" })}
                    rows={3}
                    className="text-xs font-mono resize-none"
                  />
                </div>
              </div>
            ))}
          </div>

          {createError && (
            <div className="flex items-center gap-2 text-xs text-status-error bg-status-error/10 border border-status-error/30 rounded-md px-3 py-2">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              {createError}
            </div>
          )}

          <div className="flex gap-2 justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setShowCreateForm(false); setForm(EMPTY_FORM); setCreateError(null) }}
              className="text-xs"
            >
              {t("cancel")}
            </Button>
            <Button
              size="sm"
              onClick={handleCreate}
              disabled={creating}
              className="text-xs"
            >
              {creating && <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />}
              {creating ? t("creating") : t("createExperiment")}
            </Button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 animate-spin text-wedo-cyan" />
          <span className="ml-2 text-sm text-lia-text-tertiary">{t("loadingExperiments")}</span>
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 text-sm text-status-error bg-status-error/10 border border-status-error/30 rounded-md px-4 py-3">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      ) : tests.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-lia-border-subtle rounded-md">
          <FlaskConical className="w-8 h-8 text-lia-text-tertiary mx-auto mb-2" />
          <p className="text-sm text-lia-text-secondary">{t("noActiveExperiments")}</p>
          <p className="text-xs text-lia-text-tertiary mt-1">{t("noExperimentsHint")}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {tests.map(test => {
            const metrics = metricsMap[test.test_name]
            const isExpanded = expandedTest === test.test_name
            const isLoadingMetrics = metricsLoading[test.test_name]

            return (
              <div key={test.test_name} className="border border-lia-border-subtle rounded-md overflow-hidden">
                <InteractiveSurface
                  variant="accordion"
                  aria-expanded={isExpanded}
                  className="p-4"
                  onClick={() => toggleExpand(test.test_name)}
                >
                  <div className="flex items-center gap-3">
                    <FlaskConical className="w-4 h-4 text-wedo-cyan shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-lia-text-primary">{test.test_name}</p>
                      <p className="text-xs text-lia-text-tertiary">
                        {t("variantsCountLabel", { count: test.variants.length })}
                        {test.created_at && t("createdOnLabel", { date: new Date(test.created_at).toLocaleDateString() })}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${getStatusColor(metrics)}`}>
                      {isLoadingMetrics ? "..." : getStatusLabel(metrics)}
                    </span>
                    {isExpanded
                      ? <ChevronUp className="w-4 h-4 text-lia-text-tertiary" />
                      : <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />
                    }
                  </div>
                </InteractiveSurface>

                {isExpanded && (
                  <div className="border-t border-lia-border-subtle p-4 bg-lia-bg-secondary space-y-4">
                    <div>
                      <p className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wide mb-2">{t("variantsLabel")}</p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {test.variants.map(variant => (
                          <div key={variant.variant_name} className="bg-lia-bg-primary rounded-md border border-lia-border-subtle px-3 py-2">
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-medium text-lia-text-primary">{variant.variant_name}</span>
                              <span className="text-xs text-lia-text-tertiary">{variant.traffic_percentage}%</span>
                            </div>
                            <div className="mt-1 h-1.5 bg-lia-bg-secondary rounded-full overflow-hidden">
                              <div
                                className="h-full bg-wedo-cyan rounded-full transition-[width]"
                                style={{ width: `${variant.traffic_percentage}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {isLoadingMetrics ? (
                      <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        {t("loadingMetrics")}
                      </div>
                    ) : metrics ? (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <BarChart3 className="w-3.5 h-3.5 text-wedo-cyan" />
                          <p className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wide">
                            {t("metricsHeader", { count: metrics.total_observations })}
                          </p>
                        </div>

                        {metrics.winner && (
                          <div className="flex items-center gap-2 text-xs text-status-success bg-status-success/10 border border-status-success/30 rounded-md px-3 py-2 mb-3">
                            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                            {t("winnerInline", {
                              variant: metrics.winner.variant,
                              pct: metrics.winner.improvement_pct,
                              metric: metrics.winner.metric,
                              p: metrics.winner.p_value,
                            })}
                          </div>
                        )}

                        {metrics.total_observations === 0 ? (
                          <p className="text-xs text-lia-text-tertiary">{t("noObservationsYet")}</p>
                        ) : (
                          <div className="space-y-2">
                            {Object.entries(metrics.variants).map(([variantName, variantData]) => (
                              <div key={variantName} className="bg-lia-bg-primary rounded-md border border-lia-border-subtle px-3 py-2">
                                <p className="text-xs font-medium text-lia-text-primary mb-1">{variantName}</p>
                                {Object.entries(variantData.metrics).map(([metricName, metricData]) => (
                                  <div key={metricName} className="flex items-center justify-between text-xs text-lia-text-secondary">
                                    <span>{metricName}</span>
                                    <span className="font-mono">
                                      {t("meanLabel")}: <strong>{metricData.mean}</strong> · n={metricData.sample_size}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
