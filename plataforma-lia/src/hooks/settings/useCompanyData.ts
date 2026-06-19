import { useState, useMemo, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify";
import { SETTINGS_QUERY_KEYS } from "@/hooks/settings/useSettingsBroadcast";
import {
  type CompanyData,
  type Department,
  type Approver,
  type TechStackByCategory,
  defaultCompanyData,
  parseTechStackToCategories,
  categoriesToTechStack,
} from "@/hooks/settings/department-types";

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

async function fetchCompanyProfile() {
  const res = await fetch("/api/backend-proxy/company/profile");
  if (!res.ok) throw new Error("Failed to fetch company profile");
  return res.json();
}

async function fetchCultureProfile(companyId: string) {
  const res = await fetch(
    "/api/backend-proxy/company/culture-profile/" + encodeURIComponent(companyId),
  );
  if (!res.ok) return null;
  const data = await res.json();
  return data && data.notFound ? null : data;
}

async function fetchDepartments(companyId?: string): Promise<Department[]> {
  const url = companyId
    ? `/api/backend-proxy/company/departments?company_id=${encodeURIComponent(companyId)}`
    : "/api/backend-proxy/company/departments";
  const res = await fetch(url);
  if (!res.ok) return [];
  const data = await res.json();
  if (!Array.isArray(data)) return [];
  return data.map((d: {
    id: string;
    name: string;
    description?: string;
    manager_name?: string;
    manager_title?: string;
    manager_email?: string;
    manager_phone?: string;
    headcount?: number;
    color?: string;
  }) => ({
    id: d.id,
    name: d.name,
    description: d.description || "",
    manager: d.manager_name || undefined,
    manager_title: d.manager_title || undefined,
    manager_email: d.manager_email || undefined,
    manager_phone: d.manager_phone || undefined,
    headcount: d.headcount || 0,
    color: d.color || "bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary",
  }));
}

async function fetchApprovers(companyId?: string): Promise<Approver[]> {
  const url = companyId
    ? `/api/backend-proxy/company/approvers?company_id=${encodeURIComponent(companyId)}`
    : "/api/backend-proxy/company/approvers";
  const res = await fetch(url);
  if (!res.ok) return [];
  const data = await res.json();
  if (!Array.isArray(data)) return [];
  return data.map((a: {
    id: string;
    user_id?: string;
    user_name: string;
    email: string;
    role?: string;
    level: number;
    is_active: boolean;
    department_id?: string | null;
    can_approve_above_amount?: string | number | null;
  }) => ({
    id: a.id,
    userId: a.user_id || "",
    userName: a.user_name,
    email: a.email,
    role: a.role || "",
    level: a.level,
    isActive: a.is_active,
    departmentId: a.department_id ?? null,
    canApproveAboveAmount:
      a.can_approve_above_amount === null || a.can_approve_above_amount === undefined
        ? null
        : typeof a.can_approve_above_amount === "string"
          ? parseFloat(a.can_approve_above_amount)
          : a.can_approve_above_amount,
  }));
}

function mapProfileToCompanyData(r: Record<string, unknown>): Partial<CompanyData> {
  return {
    name: (r.name as string) || defaultCompanyData.name,
    tradeName: (r.trading_name as string) || (r.name as string) || defaultCompanyData.tradeName,
    cnpj: (r.cnpj as string) || defaultCompanyData.cnpj,
    website: (r.website as string) || defaultCompanyData.website,
    email: (r.hr_email as string) || (r.main_email as string) || defaultCompanyData.email,
    phone: (r.hr_phone as string) || (r.main_phone as string) || defaultCompanyData.phone,
    address: (r.address as string) || defaultCompanyData.address,
    logo: (r.logo_url as string) || undefined,
    industry: (r.industry as string) || defaultCompanyData.industry,
    size: (r.size as string) || defaultCompanyData.size,
    employee_count: (r.employee_count as number) ?? undefined,
    company_size: (r.company_size as string) || defaultCompanyData.company_size,
    founded_year: (r.founded_year as number) ?? undefined,
    linkedin_url: (r.linkedin_url as string) || "",
    headquarters: (r.headquarters_city as string)
      ? (r.headquarters_city as string) + (r.headquarters_state ? ", " + (r.headquarters_state as string) : "")
      : "",
    additional_data: (r.additional_data as Record<string, unknown>) || undefined,
  };
}

function mergeCultureProfile(prev: CompanyData, c: Record<string, unknown>): CompanyData {
  return {
    ...prev,
    mission: (c.mission as string) || prev.mission || "",
    vision: (c.vision as string) || prev.vision || "",
    values: (c.values as string[]) || prev.values || [],
    coreCompetencies: (c.core_competencies as string[]) || prev.coreCompetencies || [],
    evp_bullets: (c.evp_bullets as string[]) || [],
    work_model: (c.work_model as string) || "",
    hybrid_days_onsite: (c.hybrid_days_onsite as number) || 3,
    employment_types: (c.employment_types as string[]) || ["CLT"],
    growth_opportunities: (c.growth_opportunities as string) || "",
    team_dynamics: (c.team_dynamics as string) || "",
    leadership_style: (c.leadership_style as string) || "",
    dei_initiatives: (c.dei_initiatives as string) || "",
    sustainability: (c.sustainability as string) || "",
    social_impact: (c.social_impact as string) || "",
    tech_stack: (c.tech_stack as string[]) || [],
    engineering_culture: (c.engineering_culture as string) || "",
    default_languages: (c.default_languages as string[]) || [],
    locations: (c.locations as string[]) || prev.locations || [],
    employee_count: (c.employee_count as number) ?? prev.employee_count,
    company_size: (c.company_size as string) || prev.company_size || "",
    headquarters: (c.headquarters as string) || prev.headquarters || "",
    founded_year: (c.founded_year as number) ?? prev.founded_year,
    linkedin_url: (c.linkedin_url as string) || prev.linkedin_url || "",
    openness_score: (c.openness_score as number) ?? prev.openness_score ?? 50,
    conscientiousness_score: (c.conscientiousness_score as number) ?? prev.conscientiousness_score ?? 50,
    extraversion_score: (c.extraversion_score as number) ?? prev.extraversion_score ?? 50,
    agreeableness_score: (c.agreeableness_score as number) ?? prev.agreeableness_score ?? 50,
    stability_score: (c.stability_score as number) ?? prev.stability_score ?? 50,
    seniority_levels: (c.seniority_levels as CompanyData["seniority_levels"]) ?? prev.seniority_levels ?? defaultCompanyData.seniority_levels,
    default_behavioral_competencies: (c.default_behavioral_competencies as CompanyData["default_behavioral_competencies"]) ?? prev.default_behavioral_competencies ?? defaultCompanyData.default_behavioral_competencies,
    default_salary_ranges: (c.default_salary_ranges as CompanyData["default_salary_ranges"]) ?? prev.default_salary_ranges ?? [],
    lia_instructions: (c.lia_instructions as CompanyData["lia_instructions"]) ?? prev.lia_instructions ?? {},
  };
}


function extractBigFive(result: Record<string, unknown>, prev?: Partial<CompanyData>) {
  const bf = result.big_five as Record<string, number> | undefined;
  return {
    openness_score: bf?.openness ?? (result.openness_score as number) ?? prev?.openness_score ?? 50,
    conscientiousness_score: bf?.conscientiousness ?? (result.conscientiousness_score as number) ?? prev?.conscientiousness_score ?? 50,
    extraversion_score: bf?.extraversion ?? (result.extraversion_score as number) ?? prev?.extraversion_score ?? 50,
    agreeableness_score: bf?.agreeableness ?? (result.agreeableness_score as number) ?? prev?.agreeableness_score ?? 50,
    stability_score: bf?.stability ?? (result.stability_score as number) ?? prev?.stability_score ?? 50,
  };
}

export function useCompanyData(): UseCompanyDataResult {
  const queryClient = useQueryClient();

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isEditingCompanyData, setIsEditingCompanyData] = useState(false);
  const [companyDataBackup, setCompanyDataBackup] = useState<CompanyData | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [isLiaAnalyzing, setIsLiaAnalyzing] = useState(false);
  const [liaAnalysisProgress, setLiaAnalysisProgress] = useState(0);
  const [liaAnalysisStep, setLiaAnalysisStep] = useState<string | null>(null);
  const [companyData, setCompanyData] = useState<CompanyData>(defaultCompanyData);
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [hasCultureProfile, setHasCultureProfile] = useState(false);

  const { data: profileData, isLoading: profileLoading } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.companyProfile(),
    queryFn: fetchCompanyProfile,
    staleTime: 60_000,
  });

  const apiCompanyId: string | null = profileData ? (profileData.id ?? null) : null;

  const { data: cultureData, isLoading: cultureLoading } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.cultureProfile(apiCompanyId ?? ""),
    queryFn: () => fetchCultureProfile(apiCompanyId!),
    enabled: !!apiCompanyId,
    staleTime: 60_000,
  });

  const { data: departmentsData, isLoading: departmentsLoading } = useQuery({
    queryKey: ["company-departments", apiCompanyId],
    queryFn: () => fetchDepartments(apiCompanyId ?? undefined),
    enabled: !!apiCompanyId,
    staleTime: 60_000,
  });

  const { data: approversData, isLoading: approversLoading } = useQuery({
    queryKey: ["company-approvers", apiCompanyId],
    queryFn: () => fetchApprovers(apiCompanyId ?? undefined),
    enabled: !!apiCompanyId,
    staleTime: 60_000,
  });

  const loading =
    profileLoading ||
    (!!apiCompanyId && cultureLoading) ||
    departmentsLoading ||
    approversLoading;

  useEffect(() => {
    if (profileData && !isEditingCompanyData) {
      setCompanyId(profileData.id ?? null);
      setCompanyData((prev) => ({ ...prev, ...mapProfileToCompanyData(profileData) }));
    }
  }, [profileData, isEditingCompanyData]);

  useEffect(() => {
    if (cultureData && !isEditingCompanyData) {
      const hasData = !!(
        cultureData.mission ||
        cultureData.vision ||
        (cultureData.values && cultureData.values.length > 0)
      );
      setHasCultureProfile(hasData);
      setCompanyData((prev) => mergeCultureProfile(prev, cultureData));
    }
  }, [cultureData, isEditingCompanyData]);

  const initialDepartments: Department[] = departmentsData ?? [];
  const initialApprovers: Approver[] = approversData ?? [];

  const techStackByCategory = useMemo(
    () => parseTechStackToCategories(companyData.tech_stack || []),
    [companyData.tech_stack],
  );

  const saveCultureData = async (data: Record<string, unknown>) => {
    const id = companyId || apiCompanyId;
    if (!id) return;
    const response = await fetch(
      "/api/backend-proxy/company/culture-profile/" + encodeURIComponent(id),
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      },
    );
    if (response.ok) {
      setHasCultureProfile(true);
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.cultureProfile(id) });
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
      notifyChatOfSettingsUpdate({ actionId: "update_company_culture", section: "company_data" });
      setSuccessMessage("Dados culturais salvos com sucesso!");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch {
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
      const id = companyId || apiCompanyId;
      const url = id
        ? "/api/backend-proxy/company/profile/" + id
        : "/api/backend-proxy/company/profile";

      const response = await fetch(url, {
        method: id ? "PUT" : "POST",
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
      if (!response.ok) throw new Error("Falha ao salvar dados da empresa");
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.companyProfile() });
      notifyChatOfSettingsUpdate({ actionId: "update_company_data", section: "company_data" });
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
      lia_instructions: { ...(prev.lia_instructions || {}), [fieldKey]: instruction },
    }));
  };

  const saveLiaToggleToBackend = async (fieldKey: string, isActive: boolean) => {
    try {
      const id = companyId || apiCompanyId || "";
      if (!id) return;
      const newToggles = { ...(companyData.lia_field_toggles || {}), [fieldKey]: isActive };
      await fetch("/api/backend-proxy/company/culture-profile/" + encodeURIComponent(id), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lia_field_toggles: newToggles }),
      });
    } catch {
      // non-critical toggle persist; swallow
    }
  };

  const updateLiaToggle = (fieldKey: string, isActive: boolean) => {
    setCompanyData((prev) => ({
      ...prev,
      lia_field_toggles: { ...(prev.lia_field_toggles || {}), [fieldKey]: isActive },
    }));
    saveLiaToggleToBackend(fieldKey, isActive);
  };

  const addTechToCategory = (category: string, tech: string) => {
    const current: TechStackByCategory = {};
    Object.keys(techStackByCategory).forEach((key) => { current[key] = [...techStackByCategory[key]]; });
    if (!current[category]) current[category] = [];
    if (!current[category].includes(tech)) {
      current[category] = [...current[category], tech];
      setCompanyData((prev) => ({ ...prev, tech_stack: categoriesToTechStack(current) }));
    }
  };

  const removeTechFromCategory = (category: string, tech: string) => {
    const current: TechStackByCategory = {};
    Object.keys(techStackByCategory).forEach((key) => { current[key] = [...techStackByCategory[key]]; });
    if (current[category]) {
      current[category] = current[category].filter((t) => t !== tech);
      setCompanyData((prev) => ({ ...prev, tech_stack: categoriesToTechStack(current) }));
    }
  };

  const getLiaAnalysisStepLabel = (progress: number): string => {
    if (progress < 15) return "Conectando...";
    if (progress < 35) return "Descobrindo páginas...";
    if (progress < 60) return "Lendo conteúdo...";
    if (progress < 95) return "Analisando...";
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
          const increment = prev < 15 ? 3 : prev < 35 ? 2 : prev < 60 ? 1.5 : 0.8;
          const newProgress = Math.min(prev + increment, 90);
          setLiaAnalysisStep(getLiaAnalysisStepLabel(newProgress));
          return newProgress;
        });
      }, 500);

      let url = companyData.website.trim();
      url = url.replace(/^httsp:\/\//i, "https://");
      url = url.replace(/^htts:\/\//i, "https://");
      if (!url.match(/^https?:\/\//i)) url = "https://" + url;

      let linkedinUrl = companyData.linkedin_url ? companyData.linkedin_url.trim() : undefined;
      if (linkedinUrl && !linkedinUrl.match(/^https?:\/\//i)) {
        linkedinUrl = "https://" + linkedinUrl;
      }

      const response = await fetch("/api/backend-proxy/company/culture-profile/analyze-direct", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          website_url: url,
          linkedin_url: linkedinUrl || undefined,
          company_id: companyId || apiCompanyId,
        }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.error || "Falha na analise");
      }
      const result = await response.json();
      setLiaAnalysisProgress(95);
      setLiaAnalysisStep("LIA analisando...");

      setCompanyData((prev) => ({
        ...prev,
        mission: result.mission || prev.mission || "",
        vision: result.vision || prev.vision || "",
        values: result.values && result.values.length > 0 ? result.values : prev.values || [],
        coreCompetencies: result.core_competencies && result.core_competencies.length > 0 ? result.core_competencies : prev.coreCompetencies || [],
        evp_bullets: result.evp_bullets && result.evp_bullets.length > 0 ? result.evp_bullets : prev.evp_bullets || [],
        growth_opportunities: result.growth_opportunities || prev.growth_opportunities || "",
        team_dynamics: result.team_dynamics || prev.team_dynamics || "",
        leadership_style: result.leadership_style || prev.leadership_style || "",
        dei_initiatives: result.dei_initiatives || prev.dei_initiatives || "",
        sustainability: result.sustainability || prev.sustainability || "",
        social_impact: result.social_impact || prev.social_impact || "",
        engineering_culture: result.engineering_culture || prev.engineering_culture || "",
        tech_stack: result.tech_stack && result.tech_stack.length > 0 ? result.tech_stack : prev.tech_stack || [],
        ...extractBigFive(result, prev),
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
          ...extractBigFive(result),
        });
        setHasCultureProfile(true);
      } catch {
        // save failure is non-critical; form already updated
      }

      setLiaAnalysisProgress(100);
      setLiaAnalysisStep("Concluido!");
      setHasCultureProfile(true);
      setSuccessMessage("Análise concluída com sucesso! Campos preenchidos automaticamente.");
      setTimeout(() => setSuccessMessage(null), 4000);
      setTimeout(() => { setLiaAnalysisProgress(0); setLiaAnalysisStep(null); }, 2000);
    } catch (err) {
      setLiaAnalysisProgress(0);
      setLiaAnalysisStep(null);
      setError(err instanceof Error ? err.message : "Erro ao analisar. Verifique a URL e tente novamente.");
      setTimeout(() => setError(null), 5000);
    } finally {
      if (progressInterval) clearInterval(progressInterval);
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
