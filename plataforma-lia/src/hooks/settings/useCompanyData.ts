import { useState, useMemo, useEffect } from "react";
import {
  type CompanyData,
  type Department,
  type Approver,
  type TechStackByCategory,
  defaultCompanyData,
  parseTechStackToCategories,
  categoriesToTechStack,
} from "@/components/settings/companyTeamHub.types";

export interface UseCompanyDataState {
  companyData: CompanyData;
  companyId: string | null;
  loading: boolean;
  saving: boolean;
  error: string | null;
  successMessage: string | null;
  hasCultureProfile: boolean;
  isEditingCompanyData: boolean;
  companyDataBackup: CompanyData | null;
  techStackByCategory: TechStackByCategory;
  expandedCategories: Record<string, boolean>;
  isLiaAnalyzing: boolean;
  liaAnalysisProgress: number;
  liaAnalysisStep: string | null;
}

export interface UseCompanyDataActions {
  setCompanyData: React.Dispatch<React.SetStateAction<CompanyData>>;
  setIsEditingCompanyData: (editing: boolean) => void;
  setCompanyDataBackup: (backup: CompanyData | null) => void;
  setExpandedCategories: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  setError: (error: string | null) => void;
  setSuccessMessage: (message: string | null) => void;
  saveCompanyData: () => Promise<void>;
  handleSaveCultureFields: () => Promise<void>;
  handleLiaAnalysis: () => Promise<void>;
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void;
  updateLiaInstruction: (fieldKey: string, instruction: string) => void;
  addTechToCategory: (category: string, tech: string) => void;
  removeTechFromCategory: (category: string, tech: string) => void;
}

export interface UseCompanyDataResult {
  state: UseCompanyDataState;
  actions: UseCompanyDataActions;
  initialDepartments: Department[];
  initialApprovers: Approver[];
}

export function useCompanyData(): UseCompanyDataResult {
  const [companyData, setCompanyData] = useState<CompanyData>(defaultCompanyData);
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [hasCultureProfile, setHasCultureProfile] = useState(false);
  const [isEditingCompanyData, setIsEditingCompanyData] = useState(false);
  const [companyDataBackup, setCompanyDataBackup] = useState<CompanyData | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [isLiaAnalyzing, setIsLiaAnalyzing] = useState(false);
  const [liaAnalysisProgress, setLiaAnalysisProgress] = useState(0);
  const [liaAnalysisStep, setLiaAnalysisStep] = useState<string | null>(null);
  const [initialDepartments, setInitialDepartments] = useState<Department[]>([]);
  const [initialApprovers, setInitialApprovers] = useState<Approver[]>([]);

  const techStackByCategory = useMemo(
    () => parseTechStackToCategories(companyData.tech_stack || []),
    [companyData.tech_stack],
  );

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [companyRes, departmentsRes, approversRes] = await Promise.all([
          fetch("/api/backend-proxy/company/profile"),
          fetch("/api/backend-proxy/company/departments"),
          fetch("/api/backend-proxy/company/approvers"),
        ]);

        let fetchedCompanyId: string | null = null;
        if (companyRes.ok) {
          const companyResult = await companyRes.json();
          if (companyResult) {
            fetchedCompanyId = companyResult.id || null;
            setCompanyId(fetchedCompanyId);
            setCompanyData({
              name: companyResult.name || defaultCompanyData.name,
              tradeName:
                companyResult.trading_name ||
                companyResult.name ||
                defaultCompanyData.tradeName,
              cnpj: companyResult.cnpj || defaultCompanyData.cnpj,
              website: companyResult.website || defaultCompanyData.website,
              email:
                companyResult.hr_email ||
                companyResult.main_email ||
                defaultCompanyData.email,
              phone:
                companyResult.hr_phone ||
                companyResult.main_phone ||
                defaultCompanyData.phone,
              address: companyResult.address || defaultCompanyData.address,
              logo: companyResult.logo_url || undefined,
              industry: companyResult.industry || defaultCompanyData.industry,
              size: companyResult.size || defaultCompanyData.size,
              employee_count: companyResult.employee_count ?? undefined,
              company_size:
                companyResult.company_size || defaultCompanyData.company_size,
              founded_year: companyResult.founded_year ?? undefined,
              linkedin_url: companyResult.linkedin_url || "",
              headquarters: companyResult.headquarters_city
                ? `${companyResult.headquarters_city}${companyResult.headquarters_state ? `, ${companyResult.headquarters_state}` : ""}`
                : "",
              additional_data: companyResult.additional_data || undefined,
            });
          }
        }

        if (departmentsRes.ok) {
          const departmentsResult = await departmentsRes.json();
          if (Array.isArray(departmentsResult) && departmentsResult.length > 0) {
            setInitialDepartments(
              departmentsResult.map((d: { id: string; name: string; description?: string; manager_name?: string; manager_title?: string; manager_email?: string; manager_phone?: string; headcount?: number; color?: string }) => ({
                id: d.id,
                name: d.name,
                description: d.description || "",
                manager: d.manager_name || undefined,
                manager_title: d.manager_title || undefined,
                manager_email: d.manager_email || undefined,
                manager_phone: d.manager_phone || undefined,
                headcount: d.headcount || 0,
                color: d.color || "bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary",
              })),
            );
          }
        }

        if (approversRes.ok) {
          const approversResult = await approversRes.json();
          if (Array.isArray(approversResult) && approversResult.length > 0) {
            setInitialApprovers(
              approversResult.map((a: { id: string; user_id?: string; user_name: string; email: string; role?: string; level: number; is_active: boolean }) => ({
                id: a.id,
                userId: a.user_id || "",
                userName: a.user_name,
                email: a.email,
                role: a.role || "",
                level: a.level,
                isActive: a.is_active,
              })),
            );
          }
        }

        if (fetchedCompanyId) {
          const cultureRes = await fetch(
            `/api/backend-proxy/company/culture-profile/${encodeURIComponent(fetchedCompanyId)}`,
          );
          if (cultureRes.ok) {
            const cultureProfile = await cultureRes.json();
            if (cultureProfile && !cultureProfile.notFound) {
              const hasData = !!(
                cultureProfile.mission ||
                cultureProfile.vision ||
                (cultureProfile.values && cultureProfile.values.length > 0)
              );
              setHasCultureProfile(hasData);
              setCompanyData((prev) => ({
                ...prev,
                mission: cultureProfile.mission || prev.mission || "",
                vision: cultureProfile.vision || prev.vision || "",
                values: cultureProfile.values || prev.values || [],
                coreCompetencies:
                  cultureProfile.core_competencies ||
                  prev.coreCompetencies ||
                  [],
                evp_bullets: cultureProfile.evp_bullets || [],
                work_model: cultureProfile.work_model || "",
                hybrid_days_onsite: cultureProfile.hybrid_days_onsite || 3,
                employment_types: cultureProfile.employment_types || ["CLT"],
                growth_opportunities: cultureProfile.growth_opportunities || "",
                team_dynamics: cultureProfile.team_dynamics || "",
                leadership_style: cultureProfile.leadership_style || "",
                dei_initiatives: cultureProfile.dei_initiatives || "",
                sustainability: cultureProfile.sustainability || "",
                social_impact: cultureProfile.social_impact || "",
                tech_stack: cultureProfile.tech_stack || [],
                engineering_culture: cultureProfile.engineering_culture || "",
                default_languages: cultureProfile.default_languages || [],
                locations: cultureProfile.locations || prev.locations || [],
                employee_count:
                  cultureProfile.employee_count ?? prev.employee_count,
                company_size:
                  cultureProfile.company_size || prev.company_size || "",
                headquarters:
                  cultureProfile.headquarters || prev.headquarters || "",
                founded_year: cultureProfile.founded_year ?? prev.founded_year,
                linkedin_url:
                  cultureProfile.linkedin_url || prev.linkedin_url || "",
                openness_score:
                  cultureProfile.openness_score ?? prev.openness_score ?? 50,
                conscientiousness_score:
                  cultureProfile.conscientiousness_score ??
                  prev.conscientiousness_score ??
                  50,
                extraversion_score:
                  cultureProfile.extraversion_score ??
                  prev.extraversion_score ??
                  50,
                agreeableness_score:
                  cultureProfile.agreeableness_score ??
                  prev.agreeableness_score ??
                  50,
                stability_score:
                  cultureProfile.stability_score ??
                  prev.stability_score ??
                  50,
                seniority_levels:
                  cultureProfile.seniority_levels ?? prev.seniority_levels ?? defaultCompanyData.seniority_levels,
                default_behavioral_competencies:
                  cultureProfile.default_behavioral_competencies ?? prev.default_behavioral_competencies ?? defaultCompanyData.default_behavioral_competencies,
                default_salary_ranges:
                  cultureProfile.default_salary_ranges ?? prev.default_salary_ranges ?? [],
                lia_instructions:
                  cultureProfile.lia_instructions ?? prev.lia_instructions ?? {},
              }));
            }
          }
        }
      } catch (err) {
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const saveCultureData = async (data: Record<string, unknown>) => {
    if (!companyId) {
      return;
    }
    try {
      const response = await fetch(
        `/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        },
      );
      if (!response.ok) {
      } else {
        setHasCultureProfile(true);
      }
    } catch (err) {
    }
  };

  const handleSaveCultureFields = async () => {
    setSaving(true);
    try {
      await saveCultureData({
        mission: companyData.mission,
        vision: companyData.vision,
        values: companyData.values,
        core_competencies: companyData.coreCompetencies,
        employee_count: companyData.employee_count,
        company_size: companyData.company_size,
        headquarters: companyData.headquarters,
        locations: companyData.locations,
        founded_year: companyData.founded_year,
        linkedin_url: companyData.linkedin_url,
        work_model: companyData.work_model,
        hybrid_days_onsite: companyData.hybrid_days_onsite,
        employment_types: companyData.employment_types,
        growth_opportunities: companyData.growth_opportunities,
        team_dynamics: companyData.team_dynamics,
        leadership_style: companyData.leadership_style,
        evp_bullets: companyData.evp_bullets,
        dei_initiatives: companyData.dei_initiatives,
        sustainability: companyData.sustainability,
        social_impact: companyData.social_impact,
        tech_stack: companyData.tech_stack,
        engineering_culture: companyData.engineering_culture,
        default_languages: companyData.default_languages,
        openness_score: companyData.openness_score,
        conscientiousness_score: companyData.conscientiousness_score,
        extraversion_score: companyData.extraversion_score,
        agreeableness_score: companyData.agreeableness_score,
        stability_score: companyData.stability_score,
      });
      setSuccessMessage("Dados culturais salvos com sucesso!");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError("Erro ao salvar dados culturais");
      setTimeout(() => setError(null), 3000);
    } finally {
      setSaving(false);
    }
  };

  const saveCompanyData = async () => {
    try {
      setSaving(true);
      setError(null);

      const url = companyId
        ? `/api/backend-proxy/company/profile/${companyId}`
        : "/api/backend-proxy/company/profile";

      const response = await fetch(url, {
        method: companyId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: companyData.name,
          trading_name: companyData.tradeName,
          cnpj: companyData.cnpj,
          website: companyData.website,
          hr_email: companyData.email,
          hr_phone: companyData.phone,
          address: companyData.address,
          logo_url: companyData.logo,
          industry: companyData.industry,
          company_size: companyData.size || companyData.company_size,
          employee_count: companyData.employee_count,
          founded_year: companyData.founded_year,
          linkedin_url: companyData.linkedin_url,
          seniority_levels: companyData.seniority_levels,
          default_behavioral_competencies: companyData.default_behavioral_competencies,
          default_salary_ranges: companyData.default_salary_ranges,
          lia_instructions: companyData.lia_instructions,
          lia_field_toggles: companyData.lia_field_toggles,
        }),
      });

      if (!response.ok) {
        throw new Error("Falha ao salvar dados da empresa");
      }

      setSuccessMessage("Dados salvos com sucesso!");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar dados");
    } finally {
      setSaving(false);
    }
  };

  const updateLiaInstruction = (fieldKey: string, instruction: string) => {
    setCompanyData((prev) => ({
      ...prev,
      lia_instructions: {
        ...(prev.lia_instructions || {}),
        [fieldKey]: instruction,
      },
    }));
  };

  const saveLiaToggleToBackend = async (fieldKey: string, isActive: boolean) => {
    try {
      let currentCompanyId = companyId || '';

      if (!currentCompanyId) {
        const profileRes = await fetch('/api/backend-proxy/company/profile');
        if (profileRes.ok) {
          const profile = await profileRes.json();
          currentCompanyId = profile.id || '';
        }
      }

      const currentToggles = companyData.lia_field_toggles || {};
      const newToggles = { ...currentToggles, [fieldKey]: isActive };

      await fetch(
        `/api/backend-proxy/company/culture-profile/${encodeURIComponent(currentCompanyId)}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lia_field_toggles: newToggles,
          }),
        }
      );
    } catch (error) {
    }
  };

  const updateLiaToggle = (fieldKey: string, isActive: boolean) => {
    setCompanyData((prev) => ({
      ...prev,
      lia_field_toggles: {
        ...(prev.lia_field_toggles || {}),
        [fieldKey]: isActive,
      },
    }));
    saveLiaToggleToBackend(fieldKey, isActive);
  };

  const addTechToCategory = (category: string, tech: string) => {
    const current: TechStackByCategory = {};
    Object.keys(techStackByCategory).forEach((key) => {
      current[key] = [...techStackByCategory[key]];
    });
    if (!current[category]) current[category] = [];
    if (!current[category].includes(tech)) {
      current[category] = [...current[category], tech];
      setCompanyData((prev) => ({
        ...prev,
        tech_stack: categoriesToTechStack(current),
      }));
    }
  };

  const removeTechFromCategory = (category: string, tech: string) => {
    const current: TechStackByCategory = {};
    Object.keys(techStackByCategory).forEach((key) => {
      current[key] = [...techStackByCategory[key]];
    });
    if (current[category]) {
      current[category] = current[category].filter((t) => t !== tech);
      setCompanyData((prev) => ({
        ...prev,
        tech_stack: categoriesToTechStack(current),
      }));
    }
  };

  const getLiaAnalysisStepLabel = (progress: number): string => {
    if (progress < 15) return "Conectando...";
    if (progress < 35) return "Descobrindo páginas...";
    if (progress < 60) return "Lendo conteúdo...";
    if (progress < 95) return "LIA analisando...";
    return "Concluído!";
  };

  const handleLiaAnalysis = async () => {
    if (!companyData.website) {
      setError("Por favor, informe o website da empresa primeiro");
      setTimeout(() => setError(null), 5000);
      return;
    }

    setIsLiaAnalyzing(true);
    setLiaAnalysisProgress(0);
    setLiaAnalysisStep("Conectando...");
    setError(null);

    let progressInterval: NodeJS.Timeout | null = null;

    try {
      progressInterval = setInterval(() => {
        setLiaAnalysisProgress((prev) => {
          if (prev >= 90) return prev;
          const increment =
            prev < 15 ? 3 : prev < 35 ? 2 : prev < 60 ? 1.5 : 0.8;
          const newProgress = Math.min(prev + increment, 90);
          setLiaAnalysisStep(getLiaAnalysisStepLabel(newProgress));
          return newProgress;
        });
      }, 500);

      let normalizedWebsiteUrl = companyData.website.trim();
      normalizedWebsiteUrl = normalizedWebsiteUrl.replace(
        /^httsp:\/\//i,
        "https://",
      );
      normalizedWebsiteUrl = normalizedWebsiteUrl.replace(
        /^htts:\/\//i,
        "https://",
      );
      if (!normalizedWebsiteUrl.match(/^https?:\/\//i)) {
        normalizedWebsiteUrl = "https://" + normalizedWebsiteUrl;
      }

      let normalizedLinkedinUrl = companyData.linkedin_url?.trim();
      if (
        normalizedLinkedinUrl &&
        !normalizedLinkedinUrl.match(/^https?:\/\//i)
      ) {
        normalizedLinkedinUrl = "https://" + normalizedLinkedinUrl;
      }

      const response = await fetch(
        "/api/backend-proxy/company/culture-profile/analyze-direct",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            website_url: normalizedWebsiteUrl,
            linkedin_url: normalizedLinkedinUrl || undefined,
            company_id: companyId,
          }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || errorData.error || "Falha na análise",
        );
      }

      const result = await response.json();

      setLiaAnalysisProgress(95);
      setLiaAnalysisStep("LIA analisando...");

      setCompanyData((prev) => ({
        ...prev,
        mission: result.mission || prev.mission || "",
        vision: result.vision || prev.vision || "",
        values: result.values?.length > 0 ? result.values : prev.values || [],
        coreCompetencies:
          result.core_competencies?.length > 0
            ? result.core_competencies
            : prev.coreCompetencies || [],
        evp_bullets:
          result.evp_bullets?.length > 0
            ? result.evp_bullets
            : prev.evp_bullets || [],
        growth_opportunities:
          result.growth_opportunities || prev.growth_opportunities || "",
        team_dynamics: result.team_dynamics || prev.team_dynamics || "",
        leadership_style:
          result.leadership_style || prev.leadership_style || "",
        dei_initiatives: result.dei_initiatives || prev.dei_initiatives || "",
        sustainability: result.sustainability || prev.sustainability || "",
        social_impact: result.social_impact || prev.social_impact || "",
        engineering_culture:
          result.engineering_culture || prev.engineering_culture || "",
        tech_stack:
          result.tech_stack?.length > 0
            ? result.tech_stack
            : prev.tech_stack || [],
        openness_score:
          result.big_five?.openness ??
          result.openness_score ??
          prev.openness_score ??
          50,
        conscientiousness_score:
          result.big_five?.conscientiousness ??
          result.conscientiousness_score ??
          prev.conscientiousness_score ??
          50,
        extraversion_score:
          result.big_five?.extraversion ??
          result.extraversion_score ??
          prev.extraversion_score ??
          50,
        agreeableness_score:
          result.big_five?.agreeableness ??
          result.agreeableness_score ??
          prev.agreeableness_score ??
          50,
        stability_score:
          result.big_five?.stability ??
          result.stability_score ??
          prev.stability_score ??
          50,
      }));

      try {
        await saveCultureData({
          mission: result.mission || "",
          vision: result.vision || "",
          values: result.values || [],
          core_competencies: result.core_competencies || [],
          evp_bullets: result.evp_bullets || [],
          growth_opportunities: result.growth_opportunities || "",
          team_dynamics: result.team_dynamics || "",
          leadership_style: result.leadership_style || "",
          dei_initiatives: result.dei_initiatives || "",
          sustainability: result.sustainability || "",
          social_impact: result.social_impact || "",
          engineering_culture: result.engineering_culture || "",
          tech_stack: result.tech_stack || [],
          openness_score:
            result.big_five?.openness ?? result.openness_score ?? 50,
          conscientiousness_score:
            result.big_five?.conscientiousness ??
            result.conscientiousness_score ??
            50,
          extraversion_score:
            result.big_five?.extraversion ?? result.extraversion_score ?? 50,
          agreeableness_score:
            result.big_five?.agreeableness ?? result.agreeableness_score ?? 50,
          stability_score:
            result.big_five?.stability ?? result.stability_score ?? 50,
        });
        setHasCultureProfile(true);
      } catch (saveErr) {
      }

      setLiaAnalysisProgress(100);
      setLiaAnalysisStep("Concluído!");
      setHasCultureProfile(true);
      setSuccessMessage(
        "Análise LIA concluída com sucesso! Campos preenchidos automaticamente.",
      );
      setTimeout(() => setSuccessMessage(null), 4000);

      setTimeout(() => {
        setLiaAnalysisProgress(0);
        setLiaAnalysisStep(null);
      }, 2000);
    } catch (err) {
      setLiaAnalysisProgress(0);
      setLiaAnalysisStep(null);
      setError(
        err instanceof Error
          ? err.message
          : "Erro ao analisar com LIA. Verifique a URL e tente novamente.",
      );
      setTimeout(() => setError(null), 5000);
    } finally {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
      setIsLiaAnalyzing(false);
    }
  };

  return {
    state: {
      companyData,
      companyId,
      loading,
      saving,
      error,
      successMessage,
      hasCultureProfile,
      isEditingCompanyData,
      companyDataBackup,
      techStackByCategory,
      expandedCategories,
      isLiaAnalyzing,
      liaAnalysisProgress,
      liaAnalysisStep,
    },
    actions: {
      setCompanyData,
      setIsEditingCompanyData,
      setCompanyDataBackup,
      setExpandedCategories,
      setError,
      setSuccessMessage,
      saveCompanyData,
      handleSaveCultureFields,
      handleLiaAnalysis,
      updateLiaToggle,
      updateLiaInstruction,
      addTechToCategory,
      removeTechFromCategory,
    },
    initialDepartments,
    initialApprovers,
  };
}
