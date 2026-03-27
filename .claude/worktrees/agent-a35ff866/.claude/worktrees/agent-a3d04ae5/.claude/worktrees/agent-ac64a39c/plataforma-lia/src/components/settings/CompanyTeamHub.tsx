"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Building,
  Users,
  Network,
  Plus,
  Edit,
  Trash2,
  Save,
  Globe,
  Mail,
  Phone,
  MapPin,
  CheckCircle,
  AlertCircle,
  Crown,
  Building2,
  Image,
  Loader2,
  Brain,
  ClipboardList,
  Briefcase,
  TrendingUp,
  Code,
  Calendar,
  Linkedin,
  Leaf,
  Heart,
  HelpCircle,
  Server,
  Layout,
  Database,
  Cloud,
  Settings,
  Palette,
  Smartphone,
  ChevronDown,
  ChevronUp,
  X,
  Maximize2,
  ExternalLink,
  Lightbulb,
  MessageSquare,
  Clock,
  User,
  FileText,
  Target,
  Settings2,
  BarChart3,
  ShieldCheck,
} from "lucide-react";
import { LiaFieldToggle, defaultLiaFieldExamples } from './LiaFieldToggle'
import { CompanyDataCard, SimpleDataCard } from './CompanyDataCard'
import { CompanyDataSection } from './CompanyDataSection'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { UserManagement } from "./user-management";
import { BenefitsTab } from "./BenefitsTab";
import { SmartImportZone } from "./SmartImportZone";
import { Gift } from "lucide-react";
import { BigFiveRadar } from "./BigFiveRadar";
import {
  INDUSTRIES,
  INDUSTRY_CATEGORIES,
  type IndustryCategory,
} from "@/lib/industry-constants";
import { textStyles, cardStyles, badgeStyles, buttonStyles, tabStyles, actionButtonStyles } from "@/lib/design-tokens";

const TECH_STACK_CATEGORIES = [
  {
    key: "backend",
    label: "Backend",
    icon: Server,
    color: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
    suggestions: [
      "Node.js",
      "Python",
      "Java",
      ".NET",
      "Go",
      "Ruby",
      "PHP",
      "Rust",
    ],
  },
  {
    key: "frontend",
    label: "Frontend",
    icon: Layout,
    color:
      "bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300",
    suggestions: [
      "React",
      "Vue.js",
      "Angular",
      "Next.js",
      "Svelte",
      "TypeScript",
      "HTML/CSS",
      "Tailwind",
    ],
  },
  {
    key: "dados",
    label: "Dados",
    icon: Database,
    color:
      "bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300",
    suggestions: [
      "PostgreSQL",
      "MongoDB",
      "MySQL",
      "Redis",
      "Elasticsearch",
      "Snowflake",
      "BigQuery",
      "Kafka",
    ],
  },
  {
    key: "cloud",
    label: "Cloud",
    icon: Cloud,
    color: "bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300",
    suggestions: [
      "AWS",
      "Azure",
      "GCP",
      "Vercel",
      "Heroku",
      "DigitalOcean",
      "Cloudflare",
    ],
  },
  {
    key: "devops",
    label: "DevOps",
    icon: Settings,
    color:
      "bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-300",
    suggestions: [
      "Docker",
      "Kubernetes",
      "Jenkins",
      "GitHub Actions",
      "Terraform",
      "Ansible",
      "GitLab CI",
    ],
  },
  {
    key: "ia_ml",
    label: "IA/ML",
    icon: Brain,
    color: "bg-pink-50 text-pink-700 dark:bg-pink-900/20 dark:text-pink-300",
    suggestions: [
      "TensorFlow",
      "PyTorch",
      "OpenAI",
      "Anthropic",
      "LangChain",
      "Hugging Face",
      "scikit-learn",
    ],
  },
  {
    key: "erps",
    label: "ERPs",
    icon: Briefcase,
    color:
      "bg-orange-50 text-orange-700 dark:bg-orange-900/20 dark:text-orange-300",
    suggestions: [
      "SAP",
      "Oracle",
      "Totvs",
      "Salesforce",
      "Dynamics 365",
      "NetSuite",
      "Workday",
    ],
  },
  {
    key: "design",
    label: "Design",
    icon: Palette,
    color: "bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-300",
    suggestions: [
      "Figma",
      "Adobe XD",
      "Sketch",
      "InVision",
      "Framer",
      "Photoshop",
      "Illustrator",
    ],
  },
  {
    key: "mobile",
    label: "Mobile",
    icon: Smartphone,
    color:
      "bg-indigo-50 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-300",
    suggestions: [
      "React Native",
      "Flutter",
      "Swift",
      "Kotlin",
      "iOS",
      "Android",
      "Expo",
    ],
  },
] as const;

type TechStackByCategory = Record<string, string[]>;

const parseTechStackToCategories = (
  techStack: string[],
): TechStackByCategory => {
  const result: TechStackByCategory = {};
  TECH_STACK_CATEGORIES.forEach((cat) => {
    result[cat.key] = [];
  });
  result["outros"] = [];

  techStack.forEach((tech) => {
    const parts = tech.split(":");
    if (parts.length === 2) {
      const [category, techName] = parts;
      if (result[category]) {
        result[category].push(techName);
      } else {
        result["outros"].push(tech);
      }
    } else {
      result["outros"].push(tech);
    }
  });
  return result;
};

const categoriesToTechStack = (categories: TechStackByCategory): string[] => {
  const result: string[] = [];
  Object.entries(categories).forEach(([category, techs]) => {
    techs.forEach((tech) => {
      if (category === "outros") {
        result.push(tech);
      } else {
        result.push(`${category}:${tech}`);
      }
    });
  });
  return result;
};

interface Department {
  id: string;
  name: string;
  description: string;
  manager?: string;
  manager_title?: string;
  manager_email?: string;
  manager_phone?: string;
  headcount: number;
  color: string;
  members?: DepartmentMember[];
}

interface DepartmentMember {
  id: string;
  name: string;
  title?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  avatar_url?: string;
  level: string;
  is_active: boolean;
}

interface Approver {
  id: string;
  userId: string;
  userName: string;
  email: string;
  role: string;
  level: number;
  isActive: boolean;
}

interface BehavioralCompetency {
  competency: string;
  weight: "Essencial" | "Importante" | "Desejável";
}

interface SalaryRange {
  department?: string;
  level: string;
  min: number;
  max: number;
  currency: string;
}

interface LiaInstructions {
  [fieldKey: string]: string;
}

interface LiaFieldToggles {
  [fieldKey: string]: boolean;
}

interface CompanyData {
  name: string;
  tradeName: string;
  cnpj: string;
  website: string;
  email: string;
  phone: string;
  address: string;
  logo?: string;
  industry: string;
  size: string;
  mission?: string;
  vision?: string;
  values?: string[];
  coreCompetencies?: string[];
  employee_count?: number;
  company_size?: string;
  headquarters?: string;
  locations?: string[];
  founded_year?: number;
  linkedin_url?: string;
  work_model?: string;
  hybrid_days_onsite?: number;
  employment_types?: string[];
  growth_opportunities?: string;
  team_dynamics?: string;
  leadership_style?: string;
  evp_bullets?: string[];
  dei_initiatives?: string;
  sustainability?: string;
  social_impact?: string;
  tech_stack?: string[];
  engineering_culture?: string;
  default_languages?: string[];
  openness_score?: number;
  conscientiousness_score?: number;
  extraversion_score?: number;
  agreeableness_score?: number;
  stability_score?: number;
  seniority_levels?: string[];
  default_behavioral_competencies?: BehavioralCompetency[];
  default_salary_ranges?: SalaryRange[];
  lia_instructions?: LiaInstructions;
  lia_field_toggles?: LiaFieldToggles;
  additional_data?: {
    hiring_volume?: number;
    job_types?: string[];
    current_ats?: string;
    main_challenges?: string[];
    main_priority?: string;
    platform_expectations?: string;
    communication_channels?: string[];
    allow_lia_contact?: boolean;
    additional_notes?: string;
    responsible_name?: string;
    responsible_position?: string;
    preferred_contact_time?: string;
    onboarding_completed_at?: string;
  };
}

interface CompanyTeamHubProps {
  activeSubsection?: string;
  onUserUpdate?: (user: any) => void;
  onGoalUpdate?: (userId: string, goals: any) => void;
}

const defaultCompanyData: CompanyData = {
  name: "WedoTalent Enterprise",
  tradeName: "WedoTalent",
  cnpj: "12.345.678/0001-90",
  website: "https://www.wedotalent.com",
  email: "contato@wedotalent.com",
  phone: "+55 11 99999-0000",
  address: "Av. Paulista, 1000 - São Paulo, SP",
  industry: "Tecnologia",
  size: "100-500",
  mission: "",
  vision: "",
  values: [],
  coreCompetencies: [],
  employee_count: undefined,
  company_size: "",
  headquarters: "",
  locations: [],
  founded_year: undefined,
  linkedin_url: "",
  work_model: "",
  hybrid_days_onsite: 3,
  employment_types: ["CLT"],
  growth_opportunities: "",
  team_dynamics: "",
  leadership_style: "",
  evp_bullets: [],
  dei_initiatives: "",
  sustainability: "",
  social_impact: "",
  tech_stack: [],
  engineering_culture: "",
  default_languages: [],
  openness_score: 50,
  conscientiousness_score: 50,
  extraversion_score: 50,
  agreeableness_score: 50,
  stability_score: 50,
  seniority_levels: ["Estágio", "Júnior", "Pleno", "Sênior", "Especialista", "Coordenador", "Gerente", "Diretor"],
  default_behavioral_competencies: [
    { competency: "Liderança", weight: "Essencial" },
    { competency: "Comunicação", weight: "Importante" },
    { competency: "Trabalho em Equipe", weight: "Importante" },
    { competency: "Resolução de Problemas", weight: "Essencial" },
    { competency: "Proatividade", weight: "Importante" },
    { competency: "Adaptabilidade", weight: "Importante" },
  ],
  default_salary_ranges: [],
  lia_instructions: {},
  lia_field_toggles: {
    work_model: true,
    seniority_levels: true,
    employment_types: true,
    salary_ranges: true,
    behavioral_competencies: true,
    engineering_culture: true,
    default_languages: true,
    company_big_five: true,
    departments: true,
    values: true,
    evp_bullets: true,
    tech_stack: true,
    leadership_style: true,
    team_dynamics: true,
    locations: true,
    trade_name: true,
    industry: true,
    website: true,
    linkedin_url: true,
    mission: true,
    vision: true,
    core_competencies: true,
    dei_initiatives: true,
    sustainability: true,
    social_impact: true,
  },
};

export function CompanyTeamHub({
  activeSubsection,
  onUserUpdate,
  onGoalUpdate,
}: CompanyTeamHubProps) {
  const [activeTab, setActiveTab] = useState(
    activeSubsection || "company-data",
  );
  const [departments, setDepartments] = useState<Department[]>([]);
  const [approvers, setApprovers] = useState<Approver[]>([]);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(
    null,
  );
  const [showDepartmentForm, setShowDepartmentForm] = useState(false);
  const [departmentToDelete, setDepartmentToDelete] =
    useState<Department | null>(null);
  const [companyData, setCompanyData] =
    useState<CompanyData>(defaultCompanyData);
  const [newDepartment, setNewDepartment] = useState({
    name: "",
    description: "",
    manager: "",
    manager_title: "",
    manager_email: "",
    manager_phone: "",
    color: "bg-gray-900 text-white",
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showApproverForm, setShowApproverForm] = useState(false);
  const [editingApprover, setEditingApprover] = useState<Approver | null>(null);
  const [newApprover, setNewApprover] = useState({
    userName: "",
    email: "",
    role: "",
    level: 1,
  });
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [hasCultureProfile, setHasCultureProfile] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<
    Record<string, boolean>
  >({});
  const [departmentMembers, setDepartmentMembers] = useState<
    DepartmentMember[]
  >([]);
  const [showMemberForm, setShowMemberForm] = useState(false);
  const [editingMember, setEditingMember] = useState<DepartmentMember | null>(
    null,
  );
  const [savingMember, setSavingMember] = useState(false);
  const [memberError, setMemberError] = useState<string | null>(null);
  const [memberSuccess, setMemberSuccess] = useState<string | null>(null);
  const [newMember, setNewMember] = useState({
    name: "",
    title: "",
    email: "",
    phone: "",
    linkedin_url: "",
    level: "outros",
  });
  const [orgChartDepartment, setOrgChartDepartment] =
    useState<Department | null>(null);
  const [orgChartMembers, setOrgChartMembers] = useState<DepartmentMember[]>(
    [],
  );
  const [loadingOrgChart, setLoadingOrgChart] = useState(false);
  const [liaAnalysisProgress, setLiaAnalysisProgress] = useState(0);
  const [liaAnalysisStep, setLiaAnalysisStep] = useState<string | null>(null);
  const [isLiaAnalyzing, setIsLiaAnalyzing] = useState(false);
  
  const [isEditingCompanyData, setIsEditingCompanyData] = useState(false);
  const [isEditingDepartments, setIsEditingDepartments] = useState(false);
  const [companyDataBackup, setCompanyDataBackup] = useState<CompanyData | null>(null);
  const [departmentsBackup, setDepartmentsBackup] = useState<Department[]>([]);

  const techStackByCategory = useMemo(
    () => parseTechStackToCategories(companyData.tech_stack || []),
    [companyData.tech_stack],
  );

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
          if (
            Array.isArray(departmentsResult) &&
            departmentsResult.length > 0
          ) {
            setDepartments(
              departmentsResult.map((d: any) => ({
                id: d.id,
                name: d.name,
                description: d.description || "",
                manager: d.manager_name || undefined,
                manager_title: d.manager_title || undefined,
                manager_email: d.manager_email || undefined,
                manager_phone: d.manager_phone || undefined,
                headcount: d.headcount || 0,
                color: d.color || "bg-gray-100 text-gray-800 dark:text-gray-200",
              })),
            );
          } else {
            setDepartments([]);
          }
        }

        if (approversRes.ok) {
          const approversResult = await approversRes.json();
          if (Array.isArray(approversResult) && approversResult.length > 0) {
            setApprovers(
              approversResult.map((a: any) => ({
                id: a.id,
                userId: a.user_id || "",
                userName: a.user_name,
                email: a.email,
                role: a.role || "",
                level: a.level,
                isActive: a.is_active,
              })),
            );
          } else {
            setApprovers([]);
          }
        }

        if (fetchedCompanyId) {
          const cultureRes = await fetch(
            `/api/backend-proxy/company/culture-profile?company_id=${fetchedCompanyId}`,
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
                  cultureProfile.stability_score ?? prev.stability_score ?? 50,
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
        console.error("Error fetching company data:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

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
        console.log("Could not save culture data from LIA analysis");
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
      console.error("LIA analysis error:", err);
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

  const saveCultureData = async (data: {
    mission?: string;
    vision?: string;
    values?: string[];
    core_competencies?: string[];
    employee_count?: number;
    company_size?: string;
    headquarters?: string;
    locations?: string[];
    founded_year?: number;
    linkedin_url?: string;
    work_model?: string;
    hybrid_days_onsite?: number;
    employment_types?: string[];
    growth_opportunities?: string;
    team_dynamics?: string;
    leadership_style?: string;
    evp_bullets?: string[];
    dei_initiatives?: string;
    sustainability?: string;
    social_impact?: string;
    tech_stack?: string[];
    engineering_culture?: string;
    default_languages?: string[];
    openness_score?: number;
    conscientiousness_score?: number;
    extraversion_score?: number;
    agreeableness_score?: number;
    stability_score?: number;
  }) => {
    if (!companyId) {
      console.log("Company ID not available, cannot save culture data");
      return;
    }
    try {
      const response = await fetch(
        `/api/backend-proxy/company/culture-profile?company_id=${companyId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        },
      );
      if (!response.ok) {
        console.log(
          "Culture profile not found, will be created on next analysis",
        );
      } else {
        setHasCultureProfile(true);
      }
    } catch (err) {
      console.error("Error saving culture data:", err);
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

  const loadDepartments = async () => {
    try {
      const response = await fetch("/api/backend-proxy/company/departments");
      if (response.ok) {
        const departmentsResult = await response.json();
        if (Array.isArray(departmentsResult) && departmentsResult.length > 0) {
          setDepartments(
            departmentsResult.map((d: any) => ({
              id: d.id,
              name: d.name,
              description: d.description || "",
              manager: d.manager_name || undefined,
              manager_title: d.manager_title || undefined,
              manager_email: d.manager_email || undefined,
              manager_phone: d.manager_phone || undefined,
              headcount: d.headcount || 0,
              color: d.color || "bg-gray-100 text-gray-800 dark:text-gray-200",
            })),
          );
        } else {
          setDepartments([]);
        }
      }
    } catch (err) {
      console.error("Error loading departments:", err);
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
      let currentCompanyId = companyId || 'default';
      
      if (!currentCompanyId || currentCompanyId === 'default') {
        const profileRes = await fetch('/api/backend-proxy/company/profile');
        if (profileRes.ok) {
          const profile = await profileRes.json();
          currentCompanyId = profile.id || 'default';
        }
      }
      
      const currentToggles = companyData.lia_field_toggles || {};
      const newToggles = { ...currentToggles, [fieldKey]: isActive };
      
      await fetch(
        `/api/backend-proxy/company/culture-profile?company_id=${currentCompanyId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lia_field_toggles: newToggles,
          }),
        }
      );
    } catch (error) {
      console.error('Error saving LIA toggle:', error);
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

  const saveDepartmentToAPI = async (dept: Department, isNew: boolean) => {
    try {
      const method = isNew ? "POST" : "PUT";
      const url = isNew
        ? "/api/backend-proxy/company/departments?company_id=default"
        : `/api/backend-proxy/company/departments/${dept.id}`;

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: dept.name,
          description: dept.description,
          manager_name: dept.manager,
          manager_title: dept.manager_title,
          manager_email: dept.manager_email,
          manager_phone: dept.manager_phone,
          headcount: dept.headcount,
          color: dept.color,
        }),
      });

      if (!response.ok) {
        throw new Error("Falha ao salvar departamento");
      }

      const result = await response.json();
      return result;
    } catch (err) {
      console.error("Error saving department:", err);
      throw err;
    }
  };

  const deleteDepartmentFromAPI = async (id: string) => {
    try {
      const response = await fetch(
        `/api/backend-proxy/company/departments/${id}`,
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        throw new Error("Falha ao remover departamento");
      }
    } catch (err) {
      console.error("Error deleting department:", err);
    }
  };

  const saveApproverToAPI = async (
    approver: { userName: string; email: string; role: string; level: number },
    isNew: boolean,
    id?: string,
  ) => {
    try {
      const method = isNew ? "POST" : "PUT";
      const url = isNew
        ? "/api/backend-proxy/company/approvers?company_id=default"
        : `/api/backend-proxy/company/approvers/${id}`;

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_name: approver.userName,
          email: approver.email,
          role: approver.role,
          level: approver.level,
        }),
      });

      if (!response.ok) {
        throw new Error("Falha ao salvar aprovador");
      }

      const result = await response.json();
      return result;
    } catch (err) {
      console.error("Error saving approver:", err);
      throw err;
    }
  };

  const deleteApproverFromAPI = async (id: string) => {
    try {
      const response = await fetch(
        `/api/backend-proxy/company/approvers/${id}`,
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        throw new Error("Falha ao remover aprovador");
      }
    } catch (err) {
      console.error("Error deleting approver:", err);
    }
  };

  const handleSaveApprover = async () => {
    if (editingApprover) {
      try {
        await saveApproverToAPI(
          {
            userName: editingApprover.userName,
            email: editingApprover.email,
            role: editingApprover.role,
            level: editingApprover.level,
          },
          false,
          editingApprover.id,
        );
        setApprovers((prev) =>
          prev.map((a) =>
            a.id === editingApprover.id ? { ...editingApprover } : a,
          ),
        );
        setEditingApprover(null);
        setSuccessMessage("Aprovador atualizado com sucesso!");
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        setError("Erro ao atualizar aprovador");
        setTimeout(() => setError(null), 3000);
      }
    } else if (newApprover.userName && newApprover.email) {
      try {
        const result = await saveApproverToAPI(newApprover, true);
        const newApproverData: Approver = {
          id: result?.id || `approver-${Date.now()}`,
          userId: result?.user_id || "",
          userName: newApprover.userName,
          email: newApprover.email,
          role: newApprover.role,
          level: newApprover.level,
          isActive: true,
        };
        setApprovers((prev) => [...prev, newApproverData]);
        setSuccessMessage("Aprovador criado com sucesso!");
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        setError("Erro ao criar aprovador");
        setTimeout(() => setError(null), 3000);
      }
      setNewApprover({
        userName: "",
        email: "",
        role: "",
        level: approvers.length + 1,
      });
      setShowApproverForm(false);
    }
  };

  const handleDeleteApprover = async (id: string) => {
    setApprovers((prev) => prev.filter((a) => a.id !== id));
    try {
      await deleteApproverFromAPI(id);
      setSuccessMessage("Aprovador removido com sucesso!");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError("Erro ao remover aprovador");
      setTimeout(() => setError(null), 3000);
    }
  };

  const tabs = [
    { id: "company-data", label: "Dados da Empresa", icon: Building },
    { id: "departments", label: "Departamentos", icon: Network },
    { id: "tech-stack", label: "Tech Stack", icon: Code },
    { id: "benefits", label: "Benefícios", icon: Gift },
    { id: "users", label: "Usuários", icon: Users },
  ];

  const colorOptions = [
    "bg-gray-900 text-white",
    "bg-wedo-green text-white",
    "bg-wedo-orange text-white",
    "bg-wedo-purple text-white",
    "bg-wedo-magenta text-white",
    "bg-[#3B82F6] text-white",
    "bg-[#EF4444] text-white",
    "bg-[#F59E0B] text-white",
  ];

  const handleSaveDepartment = async () => {
    if (!newDepartment.name) return;

    if (editingDepartment) {
      const updatedDept: Department = {
        ...editingDepartment,
        name: newDepartment.name,
        description: newDepartment.description,
        manager: newDepartment.manager,
        manager_title: newDepartment.manager_title,
        manager_email: newDepartment.manager_email,
        manager_phone: newDepartment.manager_phone,
        color: newDepartment.color,
      };
      try {
        await saveDepartmentToAPI(updatedDept, false);
        setDepartments((prev) =>
          prev.map((d) => (d.id === editingDepartment.id ? updatedDept : d)),
        );
        setSuccessMessage("Departamento atualizado com sucesso!");
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        setError("Erro ao atualizar departamento");
        setTimeout(() => setError(null), 3000);
      }
      setEditingDepartment(null);
      setNewDepartment({
        name: "",
        description: "",
        manager: "",
        manager_title: "",
        manager_email: "",
        manager_phone: "",
        color: "bg-gray-900 text-white",
      });
      setShowDepartmentForm(false);
      setDepartmentMembers([]);
      setShowMemberForm(false);
    } else {
      const dept: Department = {
        id: `dept-${Date.now()}`,
        name: newDepartment.name,
        description: newDepartment.description,
        manager: newDepartment.manager,
        manager_title: newDepartment.manager_title,
        manager_email: newDepartment.manager_email,
        manager_phone: newDepartment.manager_phone,
        headcount: 0,
        color: newDepartment.color,
      };
      try {
        const result = await saveDepartmentToAPI(dept, true);
        if (result?.id) dept.id = result.id;
        setDepartments((prev) => [...prev, dept]);
        setSuccessMessage("Departamento criado com sucesso!");
        setTimeout(() => setSuccessMessage(null), 3000);
      } catch (err) {
        setDepartments((prev) => [...prev, dept]);
      }
      setNewDepartment({
        name: "",
        description: "",
        manager: "",
        manager_title: "",
        manager_email: "",
        manager_phone: "",
        color: "bg-gray-900 text-white",
      });
      setShowDepartmentForm(false);
    }
  };

  const handleDeleteDepartment = async (id: string) => {
    setDepartments((prev) => prev.filter((d) => d.id !== id));
    try {
      await deleteDepartmentFromAPI(id);
      setSuccessMessage("Departamento removido com sucesso!");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError("Erro ao remover departamento");
      setTimeout(() => setError(null), 3000);
    }
    setDepartmentToDelete(null);
  };

  const handleStartEditDepartment = (dept: Department) => {
    setEditingDepartment(dept);
    setNewDepartment({
      name: dept.name,
      description: dept.description,
      manager: dept.manager || "",
      manager_title: dept.manager_title || "",
      manager_email: dept.manager_email || "",
      manager_phone: dept.manager_phone || "",
      color: dept.color,
    });
    setShowDepartmentForm(true);
    loadDepartmentMembers(dept.id);
  };

  const handleCancelDepartmentForm = () => {
    setShowDepartmentForm(false);
    setEditingDepartment(null);
    setNewDepartment({
      name: "",
      description: "",
      manager: "",
      manager_title: "",
      manager_email: "",
      manager_phone: "",
      color: "bg-gray-900 text-white",
    });
    setDepartmentMembers([]);
    setShowMemberForm(false);
    setEditingMember(null);
    setNewMember({
      name: "",
      title: "",
      email: "",
      phone: "",
      linkedin_url: "",
      level: "outros",
    });
  };

  const loadDepartmentMembers = async (departmentId: string) => {
    try {
      const res = await fetch(
        `/api/backend-proxy/company/departments/${departmentId}/members`,
      );
      if (res.ok) {
        const data = await res.json();
        setDepartmentMembers(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Error loading members:", err);
      setDepartmentMembers([]);
    }
  };

  const handleSaveMember = async () => {
    if (!editingDepartment || !newMember.name) {
      setMemberError("Nome do colaborador é obrigatório");
      return;
    }

    setSavingMember(true);
    setMemberError(null);
    setMemberSuccess(null);

    try {
      const url = editingMember
        ? `/api/backend-proxy/company/members/${editingMember.id}`
        : `/api/backend-proxy/company/departments/${editingDepartment.id}/members`;
      const method = editingMember ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newMember),
      });
      if (res.ok) {
        await loadDepartmentMembers(editingDepartment.id);
        setNewMember({
          name: "",
          title: "",
          email: "",
          phone: "",
          linkedin_url: "",
          level: "outros",
        });
        setShowMemberForm(false);
        setEditingMember(null);
        setMemberSuccess(
          editingMember
            ? "Colaborador atualizado com sucesso!"
            : "Colaborador adicionado com sucesso!",
        );
        setTimeout(() => setMemberSuccess(null), 3000);
      } else {
        const errorData = await res.json().catch(() => ({}));
        setMemberError(errorData.detail || "Erro ao salvar colaborador");
      }
    } catch (err) {
      console.error("Error saving member:", err);
      setMemberError("Erro de conexão. Tente novamente.");
    } finally {
      setSavingMember(false);
    }
  };

  const handleEditMember = (member: DepartmentMember) => {
    setEditingMember(member);
    setNewMember({
      name: member.name,
      title: member.title || "",
      email: member.email || "",
      phone: member.phone || "",
      linkedin_url: member.linkedin_url || "",
      level: member.level || "outros",
    });
    setShowMemberForm(true);
  };

  const handleDeleteMember = async (memberId: string) => {
    try {
      await fetch(`/api/backend-proxy/company/members/${memberId}`, {
        method: "DELETE",
      });
      if (editingDepartment) {
        await loadDepartmentMembers(editingDepartment.id);
      }
    } catch (err) {
      console.error("Error deleting member:", err);
    }
  };

  const handleOpenOrgChart = async (dept: Department) => {
    setOrgChartDepartment(dept);
    setLoadingOrgChart(true);
    try {
      const res = await fetch(
        `/api/backend-proxy/company/departments/${dept.id}/members`,
      );
      if (res.ok) {
        const data = await res.json();
        setOrgChartMembers(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Error loading org chart members:", err);
      setOrgChartMembers([]);
    } finally {
      setLoadingOrgChart(false);
    }
  };

  const getLevelOrder = (level: string): number => {
    const order: Record<string, number> = {
      ceo: 1,
      vp: 2,
      diretor: 3,
      gerente_senior: 4,
      gerente: 5,
      lider: 6,
      supervisor: 7,
      especialista: 8,
      analista: 9,
      estagiario: 10,
      outros: 11,
    };
    return order[level] || 99;
  };

  const getLevelLabel = (level: string): string => {
    const labels: Record<string, string> = {
      ceo: "CEO",
      vp: "VP",
      diretor: "Diretor",
      gerente_senior: "Gerente Sênior",
      gerente: "Gerente",
      lider: "Líder",
      supervisor: "Supervisor",
      especialista: "Especialista",
      analista: "Analista",
      estagiario: "Estagiário",
      outros: "Outros",
    };
    return labels[level] || level;
  };

  // v4.1: Cores de hierarquia em grayscale (90% gray)
  const getLevelColor = (level: string): string => {
    const colors: Record<string, string> = {
      ceo: "bg-gray-900 text-white border-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:border-gray-200",
      vp: "bg-gray-800 text-white border-gray-700 dark:bg-gray-200 dark:text-gray-900 dark:border-gray-300",
      diretor: "bg-gray-700 text-white border-gray-600 dark:bg-gray-300 dark:text-gray-900 dark:border-gray-400",
      gerente_senior: "bg-gray-600 text-white border-gray-500 dark:bg-gray-400 dark:text-gray-900 dark:border-gray-500",
      gerente: "bg-gray-500 text-white border-gray-400 dark:bg-gray-500 dark:text-white dark:border-gray-600",
      lider: "bg-gray-400 text-gray-900 border-gray-300 dark:bg-gray-600 dark:text-white dark:border-gray-700",
      supervisor: "bg-gray-300 text-gray-900 border-gray-200 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-800",
      especialista: "bg-gray-200 text-gray-800 border-gray-100 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-900",
      analista: "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700",
      estagiario: "bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-900 dark:text-gray-400 dark:border-gray-800",
      outros: "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700",
    };
    return colors[level] || "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700";
  };

  const renderCompanyData = () => {
    return (
      <CompanyDataSection
        companyData={companyData}
        setCompanyData={setCompanyData}
        isEditingCompanyData={isEditingCompanyData}
        setIsEditingCompanyData={setIsEditingCompanyData}
        companyDataBackup={companyDataBackup}
        setCompanyDataBackup={setCompanyDataBackup}
        saveCompanyData={saveCompanyData}
        saving={saving}
        loading={loading}
        successMessage={successMessage}
        error={error}
        updateLiaToggle={updateLiaToggle}
        updateLiaInstruction={updateLiaInstruction}
        isLiaAnalyzing={isLiaAnalyzing}
        liaAnalysisProgress={liaAnalysisProgress}
        liaAnalysisStep={liaAnalysisStep}
        handleLiaAnalysis={handleLiaAnalysis}
        handleSaveCultureFields={handleSaveCultureFields}
        techStackByCategory={techStackByCategory}
        expandedCategories={expandedCategories}
        setExpandedCategories={setExpandedCategories}
        addTechToCategory={addTechToCategory}
        removeTechFromCategory={removeTechFromCategory}
        TECH_STACK_CATEGORIES={TECH_STACK_CATEGORIES}
      />
    );
  };

  const renderCompanyDataOld = () => {
    if (loading) {
      return (
        <div className="space-y-3">
          <Card className="border-0 rounded-md overflow-hidden animate-pulse backdrop-blur-sm">
            <CardHeader className="bg-gray-50 dark:bg-gray-800 pb-3">
              <div className="h-5 w-48 bg-gray-200 rounded"></div>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-24 h-24 rounded-md bg-gray-200"></div>
                <div className="flex-1 grid grid-cols-2 gap-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i}>
                      <div className="h-3 w-20 bg-gray-200 rounded mb-2"></div>
                      <div className="h-10 bg-gray-200 rounded-md"></div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {successMessage && (
          <div
            className="bg-green-50 border border-green-200 text-green-700 dark:bg-green-900/20 dark:border-green-800 dark:text-green-300 px-2 py-1.5 rounded-full flex items-center gap-2 text-[11px]"
          >
            <CheckCircle className="w-3.5 h-3.5" />
            {successMessage}
          </div>
        )}
        {error && (
          <div
            className="bg-red-50 border border-red-200 text-red-700 px-2 py-1.5 rounded-full flex items-center gap-2 text-[11px]"
          >
            <AlertCircle className="w-3.5 h-3.5" />
            {error}
          </div>
        )}
        <Card className="border border-gray-200/50 dark:border-gray-700/50 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-md overflow-hidden">
          <CardHeader className="bg-gray-50/50 dark:bg-gray-800/50 pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className={`flex items-center gap-2 ${textStyles.h3}`}>
                <Building className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                Informações Institucionais
              </CardTitle>
              {!isEditingCompanyData ? (
                <button
                  onClick={() => {
                    setCompanyDataBackup({ ...companyData });
                    setIsEditingCompanyData(true);
                  }}
                  className={actionButtonStyles.smOutline}
                >
                  <Edit className={actionButtonStyles.icon} />
                  Editar
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      if (companyDataBackup) {
                        setCompanyData(companyDataBackup);
                      }
                      setIsEditingCompanyData(false);
                      setCompanyDataBackup(null);
                    }}
                    disabled={saving}
                    className={actionButtonStyles.smSecondary}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={async () => {
                      await saveCompanyData();
                      setIsEditingCompanyData(false);
                      setCompanyDataBackup(null);
                    }}
                    disabled={saving}
                    className={actionButtonStyles.smPrimary}
                  >
                    {saving ? (
                      <>
                        <Loader2 className={`${actionButtonStyles.icon} animate-spin`} />
                        Salvando...
                      </>
                    ) : (
                      <>
                        <Save className={actionButtonStyles.icon} />
                        Salvar Alterações
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-3 space-y-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <div className="w-24 h-24 rounded-md bg-gray-100 dark:bg-gray-800 border-2 border-dashed border-gray-300 flex items-center justify-center cursor-pointer hover:bg-gray-50 transition-colors hover:border-gray-400 dark:hover:border-gray-500">
                  {companyData.logo ? (
                    <img
                      src={companyData.logo}
                      alt="Logo"
                      className="w-full h-full object-cover rounded-md"
                    />
                  ) : (
                    <div className="text-center">
                      <Image className="w-8 h-8 mx-auto text-gray-600 dark:text-gray-400 mb-1" />
                      <span
                        className="text-[11px] text-gray-600"
        
                      >
                        Upload Logo
                      </span>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex-1 grid grid-cols-2 gap-3">
                <div>
                  <label
                    className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    Razão Social
                  </label>
                  <input
                    type="text"
                    value={companyData.name}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        name: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  />
                </div>
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    Nome Fantasia
                    <LiaFieldToggle
                      fieldKey="trade_name"
                      isActive={companyData.lia_field_toggles?.trade_name ?? true}
                      currentInstruction={companyData.lia_instructions?.trade_name || ''}
                      examples={defaultLiaFieldExamples.trade_name}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <input
                    type="text"
                    value={companyData.tradeName}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        tradeName: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  />
                </div>
                <div>
                  <label
                    className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    CNPJ
                  </label>
                  <input
                    type="text"
                    value={companyData.cnpj}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        cnpj: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    placeholder="00.000.000/0000-00"
    
                  />
                </div>
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    Setor
                    <LiaFieldToggle
                      fieldKey="industry"
                      isActive={companyData.lia_field_toggles?.industry ?? true}
                      currentInstruction={companyData.lia_instructions?.industry || ''}
                      examples={defaultLiaFieldExamples.industry}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <select
                    value={companyData.industry}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        industry: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  >
                    <option value="">Selecione o setor...</option>
                    {(
                      Object.keys(INDUSTRY_CATEGORIES) as IndustryCategory[]
                    ).map((category) => (
                      <optgroup
                        key={category}
                        label={INDUSTRY_CATEGORIES[category].labelPt}
                      >
                        {INDUSTRIES.filter(
                          (ind) => ind.category === category,
                        ).map((ind) => (
                          <option key={ind.key} value={ind.labelPt}>
                            {ind.labelPt}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className={`${textStyles.label} uppercase tracking-wider mb-2`}
              >
                Contato e Presença Online
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      Website
                    </span>
                    <LiaFieldToggle
                      fieldKey="website"
                      isActive={companyData.lia_field_toggles?.website ?? true}
                      currentInstruction={companyData.lia_instructions?.website || ''}
                      examples={defaultLiaFieldExamples.website}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <input
                    type="url"
                    value={companyData.website}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        website: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  />
                </div>
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      LinkedIn
                    </span>
                    <LiaFieldToggle
                      fieldKey="linkedin_url"
                      isActive={companyData.lia_field_toggles?.linkedin_url ?? true}
                      currentInstruction={companyData.lia_instructions?.linkedin_url || ''}
                      examples={defaultLiaFieldExamples.linkedin_url}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <input
                    type="url"
                    value={companyData.linkedin_url || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        linkedin_url: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    placeholder="https://linkedin.com/company/..."
    
                  />
                </div>
                <div>
                  <label
                    className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    Email
                  </label>
                  <input
                    type="email"
                    value={companyData.email}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        email: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  />
                </div>
                <div>
                  <label
                    className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    Telefone
                  </label>
                  <input
                    type="tel"
                    value={companyData.phone}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        phone: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  />
                </div>
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      Endereço
                    </span>
                    <LiaFieldToggle
                      fieldKey="locations"
                      isActive={companyData.lia_field_toggles?.locations ?? true}
                      currentInstruction={companyData.lia_instructions?.locations || ''}
                      examples={defaultLiaFieldExamples.locations}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <input
                    type="text"
                    value={companyData.address}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        address: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  />
                </div>
              </div>
            </div>

            {/* LIA Analysis Card */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <div className="rounded-md border border-gray-300 dark:border-gray-600 bg-gradient-to-r from-gray-50 dark:from-gray-900 to-transparent p-4">
                <div className="flex items-start gap-3">
                  <div
                    className="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0 bg-gray-900"
                  >
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4
                      className="text-sm font-bold text-gray-950 dark:text-gray-50 mb-1"
      
                    >
                      Análise Inteligente com LIA
                    </h4>
                    <p
                      className="text-xs text-gray-600 dark:text-gray-400 mb-3 leading-relaxed"
      
                    >
                      A LIA pode analisar o website e LinkedIn da empresa para
                      preencher automaticamente os campos de Cultura, Missão,
                      Visão, Valores e ajustar o perfil Big Five.
                    </p>

                    {isLiaAnalyzing ? (
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-xs">
                          <span
                            className="font-medium transition-all duration-300"
                          >
                            {liaAnalysisStep || "Iniciando..."}
                          </span>
                          <span
                            className="font-bold tabular-nums text-gray-700"
                          >
                            {Math.round(liaAnalysisProgress)}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden shadow-inner">
                          <div
                            className="h-2 rounded-full transition-all duration-500 ease-out relative bg-gray-900" style={{ width: `${liaAnalysisProgress}%` }}
                          >
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-pulse" />
                          </div>
                        </div>
                        <div
                          className="flex items-center gap-4 text-[10px] text-gray-500 dark:text-gray-400"
          
                        >
                          <span
                            className={
                              liaAnalysisProgress >= 0
                                ? "text-gray-600 dark:text-gray-400 font-medium"
                                : ""
                            }
                          >
                            {liaAnalysisProgress >= 15 ? "✓" : "○"} Conectando
                          </span>
                          <span
                            className={
                              liaAnalysisProgress >= 15
                                ? "text-gray-600 dark:text-gray-400 font-medium"
                                : ""
                            }
                          >
                            {liaAnalysisProgress >= 35 ? "✓" : "○"} Descobrindo
                          </span>
                          <span
                            className={
                              liaAnalysisProgress >= 35
                                ? "text-gray-600 dark:text-gray-400 font-medium"
                                : ""
                            }
                          >
                            {liaAnalysisProgress >= 60 ? "✓" : "○"} Lendo
                          </span>
                          <span
                            className={
                              liaAnalysisProgress >= 60
                                ? "text-gray-600 dark:text-gray-400 font-medium"
                                : ""
                            }
                          >
                            {liaAnalysisProgress >= 95 ? "✓" : "○"} Analisando
                          </span>
                          <span
                            className={
                              liaAnalysisProgress >= 95
                                ? "text-gray-600 dark:text-gray-400 font-medium"
                                : ""
                            }
                          >
                            {liaAnalysisProgress >= 100 ? "✓" : "○"} Concluído
                          </span>
                        </div>
                      </div>
                    ) : (
                      <Button
                        onClick={handleLiaAnalysis}
                        disabled={!isEditingCompanyData || !companyData.website}
                        className={`gap-2 text-white hover:opacity-90 transition-opacity text-xs ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''} bg-gray-900`} style={{ color: "white" }}
                      >
                        <Brain className="w-4 h-4 text-wedo-cyan" />
                        Analisar com LIA
                      </Button>
                    )}

                    {!isLiaAnalyzing && (!isEditingCompanyData || !companyData.website) && (
                      <p
                        className="text-[10px] text-amber-600 dark:text-amber-400 mt-2"
        
                      >
                        {!isEditingCompanyData 
                          ? "Clique em 'Editar' para habilitar a análise"
                          : "Informe o website da empresa acima para habilitar a análise"
                        }
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Cultura e Identidade */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <div className="flex items-center justify-between mb-3">
                <h4
                  className={`${textStyles.label} uppercase tracking-wider`}
                >
                  Cultura e Identidade
                </h4>
              </div>

              <div className="grid grid-cols-1 gap-3">
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    Missão
                    <LiaFieldToggle
                      fieldKey="mission"
                      isActive={companyData.lia_field_toggles?.mission ?? true}
                      currentInstruction={companyData.lia_instructions?.mission || ''}
                      examples={defaultLiaFieldExamples.mission}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <textarea
                    value={companyData.mission || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        mission: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    rows={2}
                    placeholder="Missão da empresa..."
    
                  />
                </div>

                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    Visão
                    <LiaFieldToggle
                      fieldKey="vision"
                      isActive={companyData.lia_field_toggles?.vision ?? true}
                      currentInstruction={companyData.lia_instructions?.vision || ''}
                      examples={defaultLiaFieldExamples.vision}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <textarea
                    value={companyData.vision || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        vision: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    rows={2}
                    placeholder="Visão da empresa..."
    
                  />
                </div>

                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    Valores
                    <LiaFieldToggle
                      fieldKey="values"
                      isActive={companyData.lia_field_toggles?.values ?? true}
                      currentInstruction={companyData.lia_instructions?.values || ''}
                      examples={defaultLiaFieldExamples.values}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(companyData.values || []).map((value, idx) => (
                      <Badge
                        key={idx}
                        className="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 text-[10px] px-2 py-0.5 rounded-full"
                      >
                        {value}
                        {isEditingCompanyData && (
                          <button
                            onClick={() =>
                              setCompanyData((prev) => ({
                                ...prev,
                                values: prev.values?.filter((_, i) => i !== idx),
                              }))
                            }
                            className="ml-1 hover:text-red-500"
                          >
                            ×
                          </button>
                        )}
                      </Badge>
                    ))}
                  </div>
                  <input
                    type="text"
                    placeholder="Adicionar valor e pressionar Enter..."
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && e.currentTarget.value.trim()) {
                        e.preventDefault();
                        setCompanyData((prev) => ({
                          ...prev,
                          values: [
                            ...(prev.values || []),
                            e.currentTarget.value.trim(),
                          ],
                        }));
                        e.currentTarget.value = "";
                      }
                    }}
                  />
                </div>

                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    Competências Comportamentais
                    <LiaFieldToggle
                      fieldKey="core_competencies"
                      isActive={companyData.lia_field_toggles?.core_competencies ?? true}
                      currentInstruction={companyData.lia_instructions?.core_competencies || ''}
                      examples={defaultLiaFieldExamples.core_competencies}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(companyData.coreCompetencies || []).map((comp, idx) => (
                      <Badge
                        key={idx}
                        className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-[10px] px-2 py-0.5 rounded-full"
                      >
                        {comp}
                        {isEditingCompanyData && (
                          <button
                            onClick={() =>
                              setCompanyData((prev) => ({
                                ...prev,
                                coreCompetencies: prev.coreCompetencies?.filter(
                                  (_, i) => i !== idx,
                                ),
                              }))
                            }
                            className="ml-1 hover:text-red-500"
                          >
                            ×
                          </button>
                        )}
                      </Badge>
                    ))}
                  </div>
                  <input
                    type="text"
                    placeholder="Adicionar competência e pressionar Enter..."
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && e.currentTarget.value.trim()) {
                        e.preventDefault();
                        setCompanyData((prev) => ({
                          ...prev,
                          coreCompetencies: [
                            ...(prev.coreCompetencies || []),
                            e.currentTarget.value.trim(),
                          ],
                        }));
                        e.currentTarget.value = "";
                      }
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Informações Corporativas */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className={`${textStyles.label} uppercase tracking-wider mb-3`}
              >
                Informações Corporativas
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div>
                  <label
                    className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <Users className="w-3 h-3 inline mr-1" />
                    Nº de Funcionários
                  </label>
                  <input
                    type="number"
                    value={companyData.employee_count || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        employee_count: parseInt(e.target.value) || undefined,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    placeholder="Ex: 500"
    
                  />
                </div>
                <div>
                  <label
                    className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <Building2 className="w-3 h-3 inline mr-1" />
                    Porte da Empresa
                  </label>
                  <select
                    value={companyData.company_size || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        company_size: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  >
                    <option value="">Selecione...</option>
                    <option value="startup">Startup (1-50)</option>
                    <option value="small">Pequena (51-200)</option>
                    <option value="medium">Média (201-1000)</option>
                    <option value="large">Grande (1001-5000)</option>
                    <option value="enterprise">Enterprise (5000+)</option>
                  </select>
                </div>
                <div>
                  <label
                    className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <Calendar className="w-3 h-3 inline mr-1" />
                    Ano de Fundação
                  </label>
                  <input
                    type="number"
                    value={companyData.founded_year || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        founded_year: parseInt(e.target.value) || undefined,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    placeholder="Ex: 2020"
    
                  />
                </div>
              </div>
            </div>

            {/* Proposta de Valor (EVP) */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className={`${textStyles.label} uppercase tracking-wider mb-3`}
              >
                Proposta de Valor (EVP)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <Briefcase className="w-3 h-3" />
                      Modelo de Trabalho
                    </span>
                    <LiaFieldToggle
                      fieldKey="work_model"
                      isActive={companyData.lia_field_toggles?.work_model ?? true}
                      currentInstruction={companyData.lia_instructions?.work_model || ''}
                      examples={defaultLiaFieldExamples.work_model}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <select
                    value={companyData.work_model || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        work_model: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  >
                    <option value="">Selecione...</option>
                    <option value="remote">100% Remoto</option>
                    <option value="hybrid">Híbrido</option>
                    <option value="onsite">Presencial</option>
                    <option value="flexible">Flexível</option>
                  </select>
                </div>
                
                {companyData.work_model === "hybrid" && (
                  <div>
                    <label
                      className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
      
                    >
                      <Calendar className="w-3 h-3 inline mr-1" />
                      Dias Presenciais por Semana
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="range"
                        min="1"
                        max="4"
                        value={companyData.hybrid_days_onsite || 3}
                        onChange={(e) =>
                          setCompanyData((prev) => ({
                            ...prev,
                            hybrid_days_onsite: parseInt(e.target.value),
                          }))
                        }
                        disabled={!isEditingCompanyData}
                        className={`flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-md appearance-none cursor-pointer accent-gray-900 dark:accent-gray-50 ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                      />
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300 min-w-[60px] text-center px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded-full">
                        {companyData.hybrid_days_onsite || 3} {(companyData.hybrid_days_onsite || 3) === 1 ? 'dia' : 'dias'}
                      </span>
                    </div>
                  </div>
                )}
                
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      Modelos de Contratação Padrão
                    </span>
                    <LiaFieldToggle
                      fieldKey="employment_types"
                      isActive={companyData.lia_field_toggles?.employment_types ?? true}
                      currentInstruction={companyData.lia_instructions?.employment_types || ''}
                      examples={defaultLiaFieldExamples.employment_types}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      { id: 'CLT', label: 'CLT' },
                      { id: 'PJ', label: 'PJ' },
                      { id: 'Freelancer', label: 'Freelancer' },
                      { id: 'Estágio', label: 'Estágio' },
                      { id: 'Temporário', label: 'Temporário' },
                      { id: 'Aprendiz', label: 'Aprendiz' },
                    ].map((type) => {
                      const isSelected = (companyData.employment_types || []).includes(type.id)
                      return (
                        <button
                          key={type.id}
                          type="button"
                          disabled={!isEditingCompanyData}
                          onClick={() => {
                            if (!isEditingCompanyData) return;
                            const current = companyData.employment_types || []
                            const updated = isSelected
                              ? current.filter(t => t !== type.id)
                              : [...current, type.id]
                            setCompanyData((prev) => ({
                              ...prev,
                              employment_types: updated,
                            }))
                          }}
                          className={`px-2 py-1 text-[10px] rounded-full border transition-colors ${
                            isSelected
                              ? 'bg-gray-100 dark:bg-gray-700 border-gray-400 dark:border-gray-500 text-gray-900 dark:text-gray-100'
                              : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300'
                          } ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
          
                        >
                          {isSelected && <CheckCircle className="w-2.5 h-2.5 inline mr-0.5" />}
                          {type.label}
                        </button>
                      )
                    })}
                  </div>
                  <p className="text-[9px] text-gray-500 dark:text-gray-500 mt-1">
                    Selecione os tipos de contratação mais usados pela empresa
                  </p>
                </div>
              </div>
            </div>

            {/* Níveis de Senioridade */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className="flex items-center gap-2 text-[10px] font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3"

              >
                Níveis de Senioridade
                <LiaFieldToggle
                  fieldKey="seniority_levels"
                  isActive={companyData.lia_field_toggles?.seniority_levels ?? true}
                  currentInstruction={companyData.lia_instructions?.seniority_levels || ''}
                  examples={defaultLiaFieldExamples.seniority_levels}
                  onToggleChange={updateLiaToggle}
                  onInstructionSave={updateLiaInstruction}
                  compact
                />
              </h4>
              <div className="space-y-2">
                <div className="flex flex-wrap gap-1.5">
                  {(companyData.seniority_levels || []).map((level, idx) => (
                    <Badge
                      key={idx}
                      className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-[10px] px-2 py-0.5 rounded-full"
                    >
                      {level}
                      {isEditingCompanyData && (
                        <button
                          onClick={() =>
                            setCompanyData((prev) => ({
                              ...prev,
                              seniority_levels: (prev.seniority_levels || []).filter((_, i) => i !== idx),
                            }))
                          }
                          className="ml-1 hover:text-red-500"
                        >
                          ×
                        </button>
                      )}
                    </Badge>
                  ))}
                </div>
                <div className="flex flex-wrap gap-1">
                  {["Estágio", "Júnior", "Pleno", "Sênior", "Especialista", "Coordenador", "Gerente", "Diretor", "C-Level"]
                    .filter((level) => !(companyData.seniority_levels || []).includes(level))
                    .map((level) => (
                      <button
                        key={level}
                        type="button"
                        disabled={!isEditingCompanyData}
                        onClick={() => {
                          if (!isEditingCompanyData) return;
                          setCompanyData((prev) => ({
                            ...prev,
                            seniority_levels: [...(prev.seniority_levels || []), level],
                          }));
                        }}
                        className={`text-[9px] px-2 py-0.5 border border-dashed border-gray-300 dark:border-gray-600 rounded-full text-gray-500 dark:text-gray-400 hover:border-purple-400 hover:text-purple-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
        
                      >
                        + {level}
                      </button>
                    ))}
                </div>
                <input
                  type="text"
                  placeholder="Adicionar nível customizado e pressionar Enter..."
                  disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
  
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.currentTarget.value.trim()) {
                      e.preventDefault();
                      const newLevel = e.currentTarget.value.trim();
                      if (!(companyData.seniority_levels || []).includes(newLevel)) {
                        setCompanyData((prev) => ({
                          ...prev,
                          seniority_levels: [...(prev.seniority_levels || []), newLevel],
                        }));
                      }
                      e.currentTarget.value = "";
                    }
                  }}
                />
                <p className="text-[9px] text-gray-500 dark:text-gray-500">
                  Defina os níveis de senioridade usados nas vagas da empresa
                </p>
              </div>
            </div>

            {/* Competências Comportamentais Padrão */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className="flex items-center gap-2 text-[10px] font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3"

              >
                Competências Comportamentais Padrão
                <LiaFieldToggle
                  fieldKey="behavioral_competencies"
                  isActive={companyData.lia_field_toggles?.behavioral_competencies ?? true}
                  currentInstruction={companyData.lia_instructions?.behavioral_competencies || ''}
                  examples={defaultLiaFieldExamples.behavioral_competencies}
                  onToggleChange={updateLiaToggle}
                  onInstructionSave={updateLiaInstruction}
                  compact
                />
              </h4>
              <div className="space-y-2">
                <div className="space-y-1.5">
                  {(companyData.default_behavioral_competencies || []).map((comp, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded-md px-3 py-1.5"
                    >
                      <span className="text-[11px] text-gray-800 dark:text-gray-200">
                        {comp.competency}
                      </span>
                      <div className="flex items-center gap-2">
                        <select
                          value={comp.weight}
                          disabled={!isEditingCompanyData}
                          onChange={(e) => {
                            const updated = [...(companyData.default_behavioral_competencies || [])];
                            updated[idx] = { ...updated[idx], weight: e.target.value as "Essencial" | "Importante" | "Desejável" };
                            setCompanyData((prev) => ({
                              ...prev,
                              default_behavioral_competencies: updated,
                            }));
                          }}
                          className={`text-[10px] px-2 py-0.5 border border-gray-200 dark:border-gray-700 rounded-full bg-white dark:bg-gray-900 ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
          
                        >
                          <option value="Essencial">Essencial</option>
                          <option value="Importante">Importante</option>
                          <option value="Desejável">Desejável</option>
                        </select>
                        {isEditingCompanyData && (
                          <button
                            onClick={() =>
                              setCompanyData((prev) => ({
                                ...prev,
                                default_behavioral_competencies: (prev.default_behavioral_competencies || []).filter((_, i) => i !== idx),
                              }))
                            }
                            className="text-gray-400 dark:text-gray-500 hover:text-red-500 transition-colors"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-1">
                  {["Liderança", "Comunicação", "Trabalho em Equipe", "Resolução de Problemas", "Proatividade", "Adaptabilidade", "Pensamento Crítico", "Orientação a Resultados", "Gestão de Tempo", "Negociação", "Criatividade", "Empatia"]
                    .filter((comp) => !(companyData.default_behavioral_competencies || []).some(c => c.competency === comp))
                    .map((comp) => (
                      <button
                        key={comp}
                        type="button"
                        disabled={!isEditingCompanyData}
                        onClick={() => {
                          if (!isEditingCompanyData) return;
                          setCompanyData((prev) => ({
                            ...prev,
                            default_behavioral_competencies: [...(prev.default_behavioral_competencies || []), { competency: comp, weight: "Importante" }],
                          }));
                        }}
                        className={`text-[9px] px-2 py-0.5 border border-dashed border-gray-300 dark:border-gray-600 rounded-full text-gray-500 dark:text-gray-400 hover:border-gray-400 hover:text-gray-700 dark:hover:border-gray-500 dark:hover:text-gray-300 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
        
                      >
                        + {comp}
                      </button>
                    ))}
                </div>
                <input
                  type="text"
                  placeholder="Adicionar competência customizada e pressionar Enter..."
                  disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
  
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.currentTarget.value.trim()) {
                      e.preventDefault();
                      const newComp = e.currentTarget.value.trim();
                      if (!(companyData.default_behavioral_competencies || []).some(c => c.competency === newComp)) {
                        setCompanyData((prev) => ({
                          ...prev,
                          default_behavioral_competencies: [...(prev.default_behavioral_competencies || []), { competency: newComp, weight: "Importante" }],
                        }));
                      }
                      e.currentTarget.value = "";
                    }
                  }}
                />
                <p className="text-[9px] text-gray-500 dark:text-gray-500">
                  Competências comportamentais que serão pré-selecionadas ao criar novas vagas
                </p>
              </div>
            </div>

            {/* Faixas Salariais Padrão */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className="flex items-center gap-2 text-[10px] font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3"

              >
                Faixas Salariais Padrão
                <LiaFieldToggle
                  fieldKey="salary_ranges"
                  isActive={companyData.lia_field_toggles?.salary_ranges ?? true}
                  currentInstruction={companyData.lia_instructions?.salary_ranges || ''}
                  examples={defaultLiaFieldExamples.salary_ranges}
                  onToggleChange={updateLiaToggle}
                  onInstructionSave={updateLiaInstruction}
                  compact
                />
              </h4>
              <div className="space-y-2">
                {(companyData.default_salary_ranges || []).length === 0 ? (
                  <p className={`${textStyles.description} py-3 text-center bg-gray-50 dark:bg-gray-800/50 rounded-md`}>
                    Nenhuma faixa salarial configurada. Adicione faixas para facilitar o preenchimento de vagas.
                  </p>
                ) : (
                  <div className="space-y-1.5">
                    {(companyData.default_salary_ranges || []).map((range, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between bg-gray-50 dark:bg-gray-800 rounded-md px-3 py-2"
                      >
                        <div className="flex items-center gap-3">
                          <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-[9px]">{range.level}</Badge>
                          {range.department && (
                            <Badge className="bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-[9px]">{range.department}</Badge>
                          )}
                          <span className="text-[11px] text-gray-800 dark:text-gray-200">
                            {range.currency} {range.min.toLocaleString('pt-BR')} - {range.max.toLocaleString('pt-BR')}
                          </span>
                        </div>
                        {isEditingCompanyData && (
                          <button
                            onClick={() =>
                              setCompanyData((prev) => ({
                                ...prev,
                                default_salary_ranges: (prev.default_salary_ranges || []).filter((_, i) => i !== idx),
                              }))
                            }
                            className="text-gray-400 dark:text-gray-500 hover:text-red-500 transition-colors"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                <div className="grid grid-cols-5 gap-2 pt-2">
                  <select
                    id="new-salary-level"
                    disabled={!isEditingCompanyData}
                    className={`col-span-1 text-[11px] px-2 py-1.5 border border-gray-200 dark:border-gray-700 rounded-full bg-white dark:bg-gray-800 ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
    
                    defaultValue=""
                  >
                    <option value="" disabled>Nível...</option>
                    {(companyData.seniority_levels || ["Júnior", "Pleno", "Sênior"]).map((level) => (
                      <option key={level} value={level}>{level}</option>
                    ))}
                  </select>
                  <input
                    id="new-salary-min"
                    type="number"
                    placeholder="Mín (R$)"
                    disabled={!isEditingCompanyData}
 className={`col-span-1 text-[11px] px-2 py-1.5 border border-gray-200 dark:border-gray-700 rounded-full bg-white ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  />
                  <input
                    id="new-salary-max"
                    type="number"
                    placeholder="Máx (R$)"
                    disabled={!isEditingCompanyData}
 className={`col-span-1 text-[11px] px-2 py-1.5 border border-gray-200 dark:border-gray-700 rounded-full bg-white ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  />
                  <input
                    id="new-salary-dept"
                    type="text"
                    placeholder="Área (opcional)"
                    disabled={!isEditingCompanyData}
 className={`col-span-1 text-[11px] px-2 py-1.5 border border-gray-200 dark:border-gray-700 rounded-full bg-white ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                  />
                  <Button
                    type="button"
                    size="sm"
                    disabled={!isEditingCompanyData}
                    className={`col-span-1 text-[10px] rounded-md bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                    onClick={() => {
                      if (!isEditingCompanyData) return;
                      const levelEl = document.getElementById('new-salary-level') as HTMLSelectElement;
                      const minEl = document.getElementById('new-salary-min') as HTMLInputElement;
                      const maxEl = document.getElementById('new-salary-max') as HTMLInputElement;
                      const deptEl = document.getElementById('new-salary-dept') as HTMLInputElement;
                      
                      if (levelEl.value && minEl.value && maxEl.value) {
                        setCompanyData((prev) => ({
                          ...prev,
                          default_salary_ranges: [
                            ...(prev.default_salary_ranges || []),
                            {
                              level: levelEl.value,
                              min: parseInt(minEl.value),
                              max: parseInt(maxEl.value),
                              currency: "R$",
                              department: deptEl.value || undefined,
                            },
                          ],
                        }));
                        levelEl.value = "";
                        minEl.value = "";
                        maxEl.value = "";
                        deptEl.value = "";
                      }
                    }}
                  >
                    <Plus className="w-3 h-3" />
                  </Button>
                </div>
                <p className="text-[9px] text-gray-500 dark:text-gray-500">
                  Faixas salariais por nível para facilitar o preenchimento de vagas
                </p>
              </div>
            </div>

            {/* Proposta de Valor (EVP) - continuação */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className={`${textStyles.label} uppercase tracking-wider mb-3`}
              >
                Proposta de Valor (EVP)
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label
                    className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <TrendingUp className="w-3 h-3 inline mr-1" />
                    Oportunidades de Crescimento
                  </label>
                  <input
                    type="text"
                    value={companyData.growth_opportunities || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        growth_opportunities: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    placeholder="Ex: Plano de carreira estruturado..."
    
                  />
                </div>
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      Dinâmica do Time
                    </span>
                    <LiaFieldToggle
                      fieldKey="team_dynamics"
                      isActive={companyData.lia_field_toggles?.team_dynamics ?? true}
                      currentInstruction={companyData.lia_instructions?.team_dynamics || ''}
                      examples={defaultLiaFieldExamples.team_dynamics}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <input
                    type="text"
                    value={companyData.team_dynamics || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        team_dynamics: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    placeholder="Ex: Colaborativo e ágil..."
    
                  />
                </div>
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <Crown className="w-3 h-3" />
                      Estilo de Liderança
                    </span>
                    <LiaFieldToggle
                      fieldKey="leadership_style"
                      isActive={companyData.lia_field_toggles?.leadership_style ?? true}
                      currentInstruction={companyData.lia_instructions?.leadership_style || ''}
                      examples={defaultLiaFieldExamples.leadership_style}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <input
                    type="text"
                    value={companyData.leadership_style || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        leadership_style: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    placeholder="Ex: Liderança servidora..."
    
                  />
                </div>
                <div className="col-span-1 md:col-span-2">
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <Heart className="w-3 h-3" />
                      Diferenciais EVP
                    </span>
                    <LiaFieldToggle
                      fieldKey="evp_bullets"
                      isActive={companyData.lia_field_toggles?.evp_bullets ?? true}
                      currentInstruction={companyData.lia_instructions?.evp_bullets || ''}
                      examples={defaultLiaFieldExamples.evp_bullets}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(companyData.evp_bullets || []).map((bullet, idx) => (
                      <Badge
                        key={idx}
                        className="bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 text-[10px] px-2 py-0.5 rounded-full"
                      >
                        {bullet}
                        {isEditingCompanyData && (
                          <button
                            onClick={() =>
                              setCompanyData((prev) => ({
                                ...prev,
                                evp_bullets: prev.evp_bullets?.filter(
                                  (_, i) => i !== idx,
                                ),
                              }))
                            }
                            className="ml-1 hover:text-red-500"
                          >
                            ×
                          </button>
                        )}
                      </Badge>
                    ))}
                  </div>
                  <input
                    type="text"
                    placeholder="Adicionar diferencial e pressionar Enter..."
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
    
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && e.currentTarget.value.trim()) {
                        e.preventDefault();
                        setCompanyData((prev) => ({
                          ...prev,
                          evp_bullets: [
                            ...(prev.evp_bullets || []),
                            e.currentTarget.value.trim(),
                          ],
                        }));
                        e.currentTarget.value = "";
                      }
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Responsabilidade Social */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className={`${textStyles.label} uppercase tracking-wider mb-3`}
              >
                Responsabilidade Social
              </h4>
              <div className="grid grid-cols-1 gap-3">
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      Iniciativas de Diversidade e Inclusão
                    </span>
                    <LiaFieldToggle
                      fieldKey="dei_initiatives"
                      isActive={companyData.lia_field_toggles?.dei_initiatives ?? true}
                      currentInstruction={companyData.lia_instructions?.dei_initiatives || ''}
                      examples={defaultLiaFieldExamples.dei_initiatives}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <textarea
                    value={companyData.dei_initiatives || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        dei_initiatives: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    rows={2}
                    placeholder="Descreva as iniciativas de D&I..."
    
                  />
                </div>
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <Leaf className="w-3 h-3" />
                      Sustentabilidade
                    </span>
                    <LiaFieldToggle
                      fieldKey="sustainability"
                      isActive={companyData.lia_field_toggles?.sustainability ?? true}
                      currentInstruction={companyData.lia_instructions?.sustainability || ''}
                      examples={defaultLiaFieldExamples.sustainability}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <textarea
                    value={companyData.sustainability || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        sustainability: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    rows={2}
                    placeholder="Descreva as práticas de sustentabilidade..."
    
                  />
                </div>
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <Heart className="w-3 h-3" />
                      Impacto Social
                    </span>
                    <LiaFieldToggle
                      fieldKey="social_impact"
                      isActive={companyData.lia_field_toggles?.social_impact ?? true}
                      currentInstruction={companyData.lia_instructions?.social_impact || ''}
                      examples={defaultLiaFieldExamples.social_impact}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <textarea
                    value={companyData.social_impact || ""}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        social_impact: e.target.value,
                      }))
                    }
                    disabled={!isEditingCompanyData}
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    rows={2}
                    placeholder="Descreva o impacto social da empresa..."
    
                  />
                </div>
              </div>
            </div>

            {/* Tecnologia */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className={`${textStyles.label} uppercase tracking-wider mb-3`}
              >
                Tecnologia
              </h4>
              <div className="grid grid-cols-1 gap-3">
                <div>
                  <label
                    className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-2"
    
                  >
                    <Code className="w-3 h-3 inline mr-1" />
                    Tech Stack por Categoria
                    <LiaFieldToggle
                      fieldKey="tech_stack"
                      isActive={companyData.lia_field_toggles?.tech_stack ?? true}
                      currentInstruction={companyData.lia_instructions?.tech_stack || ''}
                      examples={defaultLiaFieldExamples.tech_stack}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <div className="space-y-2">
                    {TECH_STACK_CATEGORIES.map((category) => {
                      const CategoryIcon = category.icon;
                      const isExpanded =
                        expandedCategories[category.key] ?? false;
                      const categoryTechs =
                        techStackByCategory[category.key] || [];

                      return (
                        <div
                          key={category.key}
                          className="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden"
                        >
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedCategories((prev) => ({
                                ...prev,
                                [category.key]: !isExpanded,
                              }))
                            }
                            className={`w-full flex items-center justify-between px-3 py-2 ${category.color} hover:opacity-90 transition-opacity`}
                          >
                            <div className="flex items-center gap-2">
                              <CategoryIcon className="w-3.5 h-3.5" />
                              <span
                                className="text-[11px] font-medium"
                
                              >
                                {category.label}
                              </span>
                              {categoryTechs.length > 0 && (
                                <Badge className="bg-white/50 dark:bg-black/20 text-[9px] px-1.5 py-0">
                                  {categoryTechs.length}
                                </Badge>
                              )}
                            </div>
                            {isExpanded ? (
                              <ChevronUp className="w-3.5 h-3.5" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5" />
                            )}
                          </button>

                          {isExpanded && (
                            <div className="p-3 bg-white dark:bg-gray-800 space-y-2">
                              {categoryTechs.length > 0 && (
                                <div className="flex flex-wrap gap-1.5">
                                  {categoryTechs.map((tech, idx) => (
                                    <Badge
                                      key={idx}
                                      className={`${category.color} text-[10px] px-2 py-0.5 rounded-full`}
                                    >
                                      {tech}
                                      {isEditingCompanyData && (
                                        <button
                                          onClick={() =>
                                            removeTechFromCategory(
                                              category.key,
                                              tech,
                                            )
                                          }
                                          className="ml-1 hover:text-red-500"
                                        >
                                          ×
                                        </button>
                                      )}
                                    </Badge>
                                  ))}
                                </div>
                              )}

                              <div className="flex flex-wrap gap-1">
                                {category.suggestions
                                  .filter((s) => !categoryTechs.includes(s))
                                  .slice(0, 6)
                                  .map((suggestion) => (
                                    <button
                                      key={suggestion}
                                      type="button"
                                      disabled={!isEditingCompanyData}
                                      onClick={() => {
                                        if (!isEditingCompanyData) return;
                                        addTechToCategory(
                                          category.key,
                                          suggestion,
                                        );
                                      }}
                                      className={`text-[9px] px-2 py-0.5 border border-dashed border-gray-300 dark:border-gray-600 rounded-full text-gray-500 dark:text-gray-400 hover:border-gray-400 hover:text-gray-700 dark:hover:border-gray-500 dark:hover:text-gray-300 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                                    >
                                      + {suggestion}
                                    </button>
                                  ))}
                              </div>

                              <input
                                type="text"
                                placeholder={`Adicionar ${category.label.toLowerCase()} personalizada...`}
                                disabled={!isEditingCompanyData}
                                className={`w-full px-2 py-1 text-[11px] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 focus:ring-1 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                
                                onKeyDown={(e) => {
                                  if (
                                    e.key === "Enter" &&
                                    e.currentTarget.value.trim()
                                  ) {
                                    e.preventDefault();
                                    addTechToCategory(
                                      category.key,
                                      e.currentTarget.value.trim(),
                                    );
                                    e.currentTarget.value = "";
                                  }
                                }}
                              />
                            </div>
                          )}
                        </div>
                      );
                    })}

                    {/* Seção Outros - para tecnologias legadas sem categoria */}
                    {techStackByCategory["outros"] &&
                      techStackByCategory["outros"].length > 0 && (
                        <div className="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedCategories((prev) => ({
                                ...prev,
                                outros: !prev.outros,
                              }))
                            }
                            className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 text-gray-800 dark:bg-gray-800 dark:text-gray-200 hover:opacity-90 transition-opacity"
                          >
                            <div className="flex items-center gap-2">
                              <Code className="w-3.5 h-3.5" />
                              <span
                                className="text-[11px] font-medium"
                
                              >
                                Outros
                              </span>
                              <Badge className="bg-white/50 dark:bg-black/20 text-[9px] px-1.5 py-0">
                                {techStackByCategory["outros"].length}
                              </Badge>
                            </div>
                            {expandedCategories.outros ? (
                              <ChevronUp className="w-3.5 h-3.5" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5" />
                            )}
                          </button>

                          {expandedCategories.outros && (
                            <div className="p-3 bg-white dark:bg-gray-800 space-y-2">
                              <div className="flex flex-wrap gap-1.5">
                                {techStackByCategory["outros"].map(
                                  (tech, idx) => (
                                    <Badge
                                      key={idx}
                                      className="bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-[10px] px-2 py-0.5 rounded-full"
                                    >
                                      {tech}
                                      {isEditingCompanyData && (
                                        <button
                                          onClick={() =>
                                            removeTechFromCategory("outros", tech)
                                          }
                                          className="ml-1 hover:text-red-500"
                                        >
                                          ×
                                        </button>
                                      )}
                                    </Badge>
                                  ),
                                )}
                              </div>

                              <input
                                type="text"
                                placeholder="Adicionar tecnologia..."
                                disabled={!isEditingCompanyData}
                                className={`w-full px-2 py-1 text-[11px] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 focus:ring-1 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                
                                onKeyDown={(e) => {
                                  if (
                                    e.key === "Enter" &&
                                    e.currentTarget.value.trim()
                                  ) {
                                    e.preventDefault();
                                    addTechToCategory(
                                      "outros",
                                      e.currentTarget.value.trim(),
                                    );
                                    e.currentTarget.value = "";
                                  }
                                }}
                              />
                            </div>
                          )}
                        </div>
                      )}
                  </div>
                </div>
                <div>
                  <label
                    className="flex items-center gap-3 text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
    
                  >
                    <span className="flex items-center gap-1">
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                      Cultura de Engenharia
                    </span>
                    <LiaFieldToggle
                      fieldKey="engineering_culture"
                      isActive={companyData.lia_field_toggles?.engineering_culture ?? true}
                      currentInstruction={companyData.lia_instructions?.engineering_culture || ''}
                      examples={defaultLiaFieldExamples.engineering_culture}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </label>
                  <textarea
                    value={companyData.engineering_culture || ""}
                    disabled={!isEditingCompanyData}
                    onChange={(e) =>
                      setCompanyData((prev) => ({
                        ...prev,
                        engineering_culture: e.target.value,
                      }))
                    }
 className={`w-full px-2 py-1.5 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
                    rows={2}
                    placeholder="Descreva a cultura de engenharia..."
    
                  />
                </div>
              </div>
            </div>

            {/* Idiomas Padrão */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <h4
                className="flex items-center gap-3 text-[10px] font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider mb-3"

              >
                Idiomas Padrão para Vagas
                <LiaFieldToggle
                  fieldKey="default_languages"
                  isActive={companyData.lia_field_toggles?.default_languages ?? true}
                  currentInstruction={companyData.lia_instructions?.default_languages || ''}
                  examples={defaultLiaFieldExamples.default_languages}
                  onToggleChange={updateLiaToggle}
                  onInstructionSave={updateLiaInstruction}
                  compact
                />
              </h4>
              <div className="space-y-2">
                <label
                  className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-2"
  
                >
                  Idiomas exigidos por padrão em novas vagas
                </label>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {(companyData.default_languages || []).map((lang, idx) => (
                    <Badge
                      key={idx}
                      className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700 text-[10px] px-2 py-0.5 rounded-full"
                    >
                      {lang}
                      {isEditingCompanyData && (
                        <button
                          onClick={() =>
                            setCompanyData((prev) => ({
                              ...prev,
                              default_languages: (prev.default_languages || []).filter((_, i) => i !== idx),
                            }))
                          }
                          className="ml-1 hover:text-red-500"
                        >
                          ×
                        </button>
                      )}
                    </Badge>
                  ))}
                </div>
                <div className="flex flex-wrap gap-1">
                  {["Português", "Inglês", "Espanhol", "Francês", "Alemão", "Italiano", "Mandarim", "Japonês"]
                    .filter((lang) => !(companyData.default_languages || []).includes(lang))
                    .map((lang) => (
                      <button
                        key={lang}
                        type="button"
                        disabled={!isEditingCompanyData}
                        onClick={() => {
                          if (!isEditingCompanyData) return;
                          setCompanyData((prev) => ({
                            ...prev,
                            default_languages: [...(prev.default_languages || []), lang],
                          }));
                        }}
                        className={`text-[9px] px-2 py-0.5 border border-dashed border-gray-300 dark:border-gray-600 rounded-full text-gray-500 dark:text-gray-400 hover:border-gray-400 hover:text-gray-700 dark:hover:border-gray-500 dark:hover:text-gray-300 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
        
                      >
                        + {lang}
                      </button>
                    ))}
                </div>
                <input
                  type="text"
                  placeholder="Adicionar outro idioma..."
                  disabled={!isEditingCompanyData}
                  className={`w-full px-2 py-1 text-[11px] border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 focus:ring-1 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors mt-2 ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
  
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.currentTarget.value.trim()) {
                      e.preventDefault();
                      const newLang = e.currentTarget.value.trim();
                      if (!(companyData.default_languages || []).includes(newLang)) {
                        setCompanyData((prev) => ({
                          ...prev,
                          default_languages: [...(prev.default_languages || []), newLang],
                        }));
                      }
                      e.currentTarget.value = "";
                    }
                  }}
                />
              </div>
            </div>

            {/* Perfil Organizacional (Big Five) */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-1.5">
                  <h4
                    className="flex items-center gap-2 text-[10px] font-semibold text-gray-900 dark:text-gray-50 uppercase tracking-wider"
    
                  >
                    Perfil Organizacional (Big Five)
                    <LiaFieldToggle
                      fieldKey="company_big_five"
                      isActive={companyData.lia_field_toggles?.company_big_five ?? true}
                      currentInstruction={companyData.lia_instructions?.company_big_five || ''}
                      examples={defaultLiaFieldExamples.company_big_five}
                      onToggleChange={updateLiaToggle}
                      onInstructionSave={updateLiaInstruction}
                      compact
                    />
                  </h4>
                  <Popover>
                    <PopoverTrigger asChild>
                      <button
                        type="button"
                        className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                      >
                        <HelpCircle className="w-3.5 h-3.5" />
                      </button>
                    </PopoverTrigger>
                    <PopoverContent
                      side="right"
                      className="max-w-xs text-[11px] p-3"
                    >
                      <p>
                        <strong className="block mb-1">
                          Como a LIA infere o Big Five?
                        </strong>
                        A LIA analisa o website corporativo, cultura declarada,
                        missão, visão e valores da empresa. Os 5 traços medem:
                      </p>
                      <ul className="mt-2 space-y-1 text-[10px] text-gray-600 dark:text-gray-400">
                        <li>
                          <strong>Abertura:</strong> Inovação e criatividade
                        </li>
                        <li>
                          <strong>Conscienciosidade:</strong> Processos e
                          organização
                        </li>
                        <li>
                          <strong>Extroversão:</strong> Colaboração e energia
                        </li>
                        <li>
                          <strong>Amabilidade:</strong> Empatia e trabalho em
                          equipe
                        </li>
                        <li>
                          <strong>Estabilidade:</strong> Resiliência e calma
                        </li>
                      </ul>
                      <p
                        className="mt-2 text-[10px] text-gray-500 dark:text-gray-400"
        
                      >
                        Você pode ajustar manualmente os valores arrastando os
                        sliders.
                      </p>
                    </PopoverContent>
                  </Popover>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveCultureFields}
                  disabled={saving}
                  className="text-[10px] rounded-md border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  {saving ? (
                    <>
                      <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Save className="w-3 h-3 mr-1.5" />
                      Salvar Perfil Cultural
                    </>
                  )}
                </Button>
              </div>
              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-4">
                <BigFiveRadar
                  scores={{
                    openness: companyData.openness_score ?? 50,
                    conscientiousness:
                      companyData.conscientiousness_score ?? 50,
                    extraversion: companyData.extraversion_score ?? 50,
                    agreeableness: companyData.agreeableness_score ?? 50,
                    stability: companyData.stability_score ?? 50,
                  }}
                  onScoresChange={(scores) => {
                    if (!isEditingCompanyData) return;
                    setCompanyData((prev) => ({
                      ...prev,
                      openness_score: scores.openness,
                      conscientiousness_score: scores.conscientiousness,
                      extraversion_score: scores.extraversion,
                      agreeableness_score: scores.agreeableness,
                      stability_score: scores.stability,
                    }));
                  }}
                  isEditable={isEditingCompanyData}
                  size={200}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderDepartments = () => (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="flex items-center gap-2 text-[13px] font-semibold text-gray-950 dark:text-gray-50">
            Departamentos
            <LiaFieldToggle
              fieldKey="departments"
              isActive={companyData.lia_field_toggles?.departments ?? true}
              currentInstruction={companyData.lia_instructions?.departments || ''}
              examples={defaultLiaFieldExamples.departments}
              onToggleChange={updateLiaToggle}
              onInstructionSave={updateLiaInstruction}
              compact
            />
          </h3>
          <p
            className="text-[11px] text-gray-600"
          >
            Gerencie a estrutura organizacional da empresa
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!isEditingDepartments ? (
            <button
              onClick={() => {
                setDepartmentsBackup([...departments]);
                setIsEditingDepartments(true);
              }}
              className={actionButtonStyles.smOutline}
            >
              <Edit className={actionButtonStyles.icon} />
              Editar
            </button>
          ) : (
            <>
              <button
                onClick={() => {
                  setDepartments(departmentsBackup);
                  setIsEditingDepartments(false);
                  setDepartmentsBackup([]);
                  setShowDepartmentForm(false);
                  setEditingDepartment(null);
                }}
                disabled={saving}
                className={actionButtonStyles.smSecondary}
              >
                Cancelar
              </button>
              <button
                onClick={async () => {
                  setIsEditingDepartments(false);
                  setDepartmentsBackup([]);
                }}
                disabled={saving}
                className={actionButtonStyles.smPrimary}
              >
                {saving ? (
                  <>
                    <Loader2 className={`${actionButtonStyles.icon} animate-spin`} />
                    Salvando...
                  </>
                ) : (
                  <>
                    <Save className={actionButtonStyles.icon} />
                    Salvar Alterações
                  </>
                )}
              </button>
              <Button
                onClick={() => setShowDepartmentForm(true)}
                size="sm"
                className="gap-1.5 py-1.5 px-2 text-[11px] rounded-full bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              >
                <Plus className="w-3.5 h-3.5" />
                Novo Departamento
              </Button>
            </>
          )}
        </div>
      </div>

      <SmartImportZone
        title="Importar Departamentos"
        description="Arraste uma planilha Excel ou CSV com o organograma da empresa. A LIA vai identificar automaticamente os departamentos, gestores e hierarquias."
        importEndpoint="/api/backend-proxy/company/departments/import"
        templateDownloadEndpoint="/api/backend-proxy/company/departments/import/template"
        expectedFields={[
          "name",
          "description",
          "manager",
          "manager_email",
          "parent_department",
          "headcount",
          "cost_center",
          "order",
        ]}
        onImportSuccess={() => {
          loadDepartments();
        }}
        disabled={!isEditingDepartments}
      />

      {showDepartmentForm && isEditingDepartments && (
        <Card className="border-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-md">
          <CardContent className="p-3 space-y-2">
            <div className="flex items-center justify-between mb-2">
              <h4
                className="text-xs font-semibold text-gray-950 dark:text-gray-50"

              >
                {editingDepartment
                  ? "Editar Departamento"
                  : "Novo Departamento"}
              </h4>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 rounded-md"
                onClick={handleCancelDepartmentForm}
              >
                <X className="w-3.5 h-3.5" />
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label
                  className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
  
                >
                  Nome
                </label>
                <input
                  type="text"
                  value={newDepartment.name}
                  onChange={(e) =>
                    setNewDepartment((prev) => ({
                      ...prev,
                      name: e.target.value,
                    }))
                  }
                  className="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
                  placeholder="Ex: Engenharia"
  
                />
              </div>
              <div>
                <label
                  className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
  
                >
                  Gestor
                </label>
                <input
                  type="text"
                  value={newDepartment.manager}
                  onChange={(e) =>
                    setNewDepartment((prev) => ({
                      ...prev,
                      manager: e.target.value,
                    }))
                  }
                  className="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
                  placeholder="Nome do gestor"
  
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label
                  className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
  
                >
                  Cargo do Gestor
                </label>
                <input
                  type="text"
                  value={newDepartment.manager_title}
                  onChange={(e) =>
                    setNewDepartment((prev) => ({
                      ...prev,
                      manager_title: e.target.value,
                    }))
                  }
                  className="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
                  placeholder="Ex: Diretor de Engenharia"
  
                />
              </div>
              <div>
                <label
                  className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
  
                >
                  Email do Gestor
                </label>
                <input
                  type="email"
                  value={newDepartment.manager_email}
                  onChange={(e) =>
                    setNewDepartment((prev) => ({
                      ...prev,
                      manager_email: e.target.value,
                    }))
                  }
                  className="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
                  placeholder="gestor@empresa.com"
  
                />
              </div>
              <div>
                <label
                  className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
  
                >
                  Telefone/WhatsApp
                </label>
                <input
                  type="text"
                  value={newDepartment.manager_phone}
                  onChange={(e) =>
                    setNewDepartment((prev) => ({
                      ...prev,
                      manager_phone: e.target.value,
                    }))
                  }
                  className="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
                  placeholder="+55 11 99999-0000"
  
                />
              </div>
            </div>
            <div>
              <label
                className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"

              >
                Descrição
              </label>
              <textarea
                value={newDepartment.description}
                onChange={(e) =>
                  setNewDepartment((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                className="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
                rows={2}
                placeholder="Descrição do departamento"

              />
            </div>
            <div>
              <label
                className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"

              >
                Cor
              </label>
              <div className="flex gap-2">
                {colorOptions.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() =>
                      setNewDepartment((prev) => ({ ...prev, color }))
                    }
                    className={`w-4 h-4 rounded-full ${color.split(" ")[0]} ${newDepartment.color === color ? "ring-2 ring-offset-2 ring-gray-900 dark:ring-gray-50" : ""}`}
                  />
                ))}
              </div>
            </div>

            {editingDepartment && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-3 mt-3">
                <div className="flex items-center justify-between mb-2">
                  <h5
                    className="text-[11px] font-semibold text-gray-800 dark:text-gray-200"
    
                  >
                    Colaboradores do Departamento
                  </h5>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setShowMemberForm(true);
                      setEditingMember(null);
                      setNewMember({
                        name: "",
                        title: "",
                        email: "",
                        phone: "",
                        linkedin_url: "",
                        level: "outros",
                      });
                    }}
                    disabled={!isEditingDepartments}
                    className={`py-1 px-2 text-[10px] rounded-full border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 ${!isEditingDepartments ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    Adicionar
                  </Button>
                </div>

                <div className="space-y-2 max-h-[200px] overflow-y-auto">
                  {departmentMembers.length === 0 ? (
                    <p
                      className="text-[10px] text-gray-500 text-center py-3"
      
                    >
                      Nenhum colaborador cadastrado
                    </p>
                  ) : (
                    departmentMembers.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center justify-between p-2 bg-gray-50 rounded-md"
                      >
                        <div className="flex items-center gap-2">
                          <Avatar className="w-7 h-7">
                            <AvatarFallback className="text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                              {member.name.charAt(0).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p
                              className="text-[11px] font-medium text-gray-950 dark:text-gray-50"
              
                            >
                              {member.name}
                            </p>
                            <p
                              className="text-[10px] text-gray-500"
              
                            >
                              {member.title || "Sem cargo"} • {member.level}
                            </p>
                          </div>
                        </div>
                        {isEditingDepartments && (
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditMember(member)}
                              className="h-6 w-6 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                            >
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteMember(member.id)}
                              className="h-6 w-6 p-0 rounded-md text-red-500 hover:text-red-600 hover:bg-red-50"
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>

                {showMemberForm && (
                  <div className="mt-2 p-2 border border-gray-200 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800">
                    <h6
                      className="text-[10px] font-medium text-gray-600 mb-2"
      
                    >
                      {editingMember
                        ? "Editar Colaborador"
                        : "Novo Colaborador"}
                    </h6>
                    <div className="grid grid-cols-2 gap-2 mb-2">
                      <input
                        type="text"
                        placeholder="Nome"
                        value={newMember.name}
                        onChange={(e) =>
                          setNewMember((prev) => ({
                            ...prev,
                            name: e.target.value,
                          }))
                        }
                        className="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
        
                      />
                      <input
                        type="text"
                        placeholder="Cargo"
                        value={newMember.title}
                        onChange={(e) =>
                          setNewMember((prev) => ({
                            ...prev,
                            title: e.target.value,
                          }))
                        }
                        className="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
        
                      />
                      <input
                        type="email"
                        placeholder="Email"
                        value={newMember.email}
                        onChange={(e) =>
                          setNewMember((prev) => ({
                            ...prev,
                            email: e.target.value,
                          }))
                        }
                        className="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
        
                      />
                      <input
                        type="text"
                        placeholder="Telefone"
                        value={newMember.phone}
                        onChange={(e) =>
                          setNewMember((prev) => ({
                            ...prev,
                            phone: e.target.value,
                          }))
                        }
                        className="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors"
        
                      />
                      <input
                        type="url"
                        placeholder="LinkedIn URL"
                        value={newMember.linkedin_url}
                        onChange={(e) =>
                          setNewMember((prev) => ({
                            ...prev,
                            linkedin_url: e.target.value,
                          }))
                        }
                        className="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors col-span-2"
        
                      />
                      <select
                        value={newMember.level}
                        onChange={(e) =>
                          setNewMember((prev) => ({
                            ...prev,
                            level: e.target.value,
                          }))
                        }
                        className="w-full px-2 py-1.5 text-[11px] border border-gray-200 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors col-span-2"
        
                      >
                        <option value="ceo">CEO</option>
                        <option value="vp">VP</option>
                        <option value="diretor">Diretor</option>
                        <option value="gerente_senior">Gerente Sênior</option>
                        <option value="gerente">Gerente</option>
                        <option value="lider">Líder</option>
                        <option value="supervisor">Supervisor</option>
                        <option value="especialista">Especialista</option>
                        <option value="analista">Analista</option>
                        <option value="estagiario">Estagiário</option>
                        <option value="outros">Outros</option>
                      </select>
                    </div>
                    {memberError && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-2 flex items-center gap-2 text-red-700 text-[10px]">
                        <AlertCircle className="w-3 h-3" />
                        {memberError}
                      </div>
                    )}
                    {memberSuccess && (
                      <div className="bg-green-50 border border-green-200 rounded-md p-2 flex items-center gap-2 text-green-700 text-[10px]">
                        <CheckCircle className="w-3 h-3" />
                        {memberSuccess}
                      </div>
                    )}
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setShowMemberForm(false);
                          setEditingMember(null);
                          setNewMember({
                            name: "",
                            title: "",
                            email: "",
                            phone: "",
                            linkedin_url: "",
                            level: "outros",
                          });
                          setMemberError(null);
                        }}
                        className="py-1 px-2 text-[10px] rounded-full"
        
                        disabled={savingMember}
                      >
                        Cancelar
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleSaveMember}
                        className="py-1 px-2 text-[10px] rounded-full bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                        disabled={savingMember}
                      >
                        {savingMember ? (
                          <>
                            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            Salvando...
                          </>
                        ) : (
                          "Salvar"
                        )}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancelDepartmentForm}
                className="py-1.5 px-2 text-[11px] rounded-full"

              >
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleSaveDepartment}
                className="py-1.5 px-2 text-[11px] rounded-full bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              >
                <Save className="w-3.5 h-3.5 mr-1" />
                {editingDepartment ? "Atualizar" : "Salvar"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-md p-2 flex items-center gap-2 text-green-700 text-[11px]">
          <CheckCircle className="w-3.5 h-3.5" />
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-2 flex items-center gap-2 text-red-700 text-[11px]">
          <AlertCircle className="w-3.5 h-3.5" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {departments.length === 0 && !showDepartmentForm ? (
          <div className="col-span-2 text-center py-8 text-gray-600">
            <Network className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
              Nenhum departamento cadastrado
            </p>
            <p className="text-[11px] mt-1 text-gray-500 dark:text-gray-500">
              Clique em "Novo Departamento" ou importe uma planilha para começar
            </p>
          </div>
        ) : (
          departments.map((dept) => (
            <Card
              key={dept.id}
              className="border border-gray-200/50 dark:border-gray-700/50 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-md hover:transition-shadow"
            >
              <CardContent className="p-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-9 h-9 rounded-md ${dept.color} flex items-center justify-center`}
                    >
                      <Building2 className="w-4 h-4" />
                    </div>
                    <div>
                      <h4
                        className="text-xs font-semibold text-gray-950 dark:text-gray-50"
        
                      >
                        {dept.name}
                      </h4>
                      <p
                        className="text-[10px] text-gray-600"
        
                      >
                        {dept.description}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => handleOpenOrgChart(dept)}
                      title="Ver organograma"
                    >
                      <Maximize2 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                      onClick={() => handleStartEditDepartment(dept)}
                      disabled={!isEditingDepartments}
                    >
                      <Edit className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 rounded-md text-red-500 hover:text-red-600 hover:bg-red-50"
                      onClick={() => setDepartmentToDelete(dept)}
                      disabled={!isEditingDepartments}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
                  <div
                    className="flex items-center gap-2 text-[10px] text-gray-600"
    
                  >
                    <Users className="w-3 h-3" />
                    <span>{dept.headcount} colaboradores</span>
                  </div>
                  {dept.manager && (
                    <Badge
                      variant="outline"
                      className="text-[10px] rounded-md border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300"
                    >
                      {dept.manager}
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <AlertDialog
        open={!!departmentToDelete}
        onOpenChange={() => setDepartmentToDelete(null)}
      >
        <AlertDialogContent className="rounded-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-[14px] font-semibold text-gray-900 dark:text-gray-50">
              Excluir Departamento
            </AlertDialogTitle>
            <AlertDialogDescription
            >
              Tem certeza que deseja excluir o departamento "
              {departmentToDelete?.name}"? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              className="rounded-md text-[11px]"
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              className="rounded-md text-[11px] bg-red-500 hover:bg-red-600"
              onClick={() =>
                departmentToDelete &&
                handleDeleteDepartment(departmentToDelete.id)
              }
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog
        open={!!orgChartDepartment}
        onOpenChange={() => setOrgChartDepartment(null)}
      >
        <DialogContent className="rounded-md max-w-4xl max-h-[85vh] overflow-hidden">
          <DialogHeader>
            <div className="flex items-center gap-3">
              <div
                className={`w-10 h-10 rounded-md ${orgChartDepartment?.color || "bg-gray-900 text-white"} flex items-center justify-center`}
              >
                <Network className="w-5 h-5" />
              </div>
              <div>
                <DialogTitle
  
                  className="text-[15px]"
                >
                  Organograma - {orgChartDepartment?.name}
                </DialogTitle>
                <p
                  className={`${textStyles.description} mt-0.5`}
                >
                  {orgChartMembers.length} colaboradores cadastrados
                </p>
              </div>
            </div>
          </DialogHeader>

          <div className="overflow-y-auto max-h-[60vh] mt-4">
            {loadingOrgChart ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-gray-500 dark:text-gray-400" />
              </div>
            ) : orgChartMembers.length === 0 ? (
              <div className="text-center py-12">
                <Users className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p
                  className="text-xs font-medium text-gray-600"
  
                >
                  Nenhum colaborador cadastrado
                </p>
                <p
                  className={`${textStyles.description} mt-1`}
                >
                  Adicione colaboradores através da edição do departamento
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {Object.entries(
                  orgChartMembers
                    .sort(
                      (a, b) => getLevelOrder(a.level) - getLevelOrder(b.level),
                    )
                    .reduce(
                      (acc, member) => {
                        const level = member.level || "outros";
                        if (!acc[level]) acc[level] = [];
                        acc[level].push(member);
                        return acc;
                      },
                      {} as Record<string, DepartmentMember[]>,
                    ),
                )
                  .sort(([a], [b]) => getLevelOrder(a) - getLevelOrder(b))
                  .map(([level, members]) => (
                    <div key={level} className="space-y-2">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge
                          className={`text-[10px] px-2 py-0.5 rounded-full border ${getLevelColor(level)}`}
          
                        >
                          {getLevelLabel(level)}
                        </Badge>
                        <div className="flex-1 h-px bg-gray-200"></div>
                        <span
                          className="text-[10px] text-gray-400"
          
                        >
                          {members.length}{" "}
                          {members.length === 1 ? "pessoa" : "pessoas"}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                        {members.map((member) => (
                          <div
                            key={member.id}
                            className="flex items-center gap-3 p-3 bg-white border border-gray-100 rounded-md hover:transition-shadow"
                          >
                            <Avatar className="w-10 h-10">
                              {member.avatar_url ? (
                                <img
                                  src={member.avatar_url}
                                  alt={member.name}
                                  className="w-full h-full object-cover rounded-full"
                                />
                              ) : (
                                <AvatarFallback className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                                  {member.name
                                    .split(" ")
                                    .map((n) => n[0])
                                    .slice(0, 2)
                                    .join("")
                                    .toUpperCase()}
                                </AvatarFallback>
                              )}
                            </Avatar>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5">
                                <p
                                  className="text-xs font-medium text-gray-950 dark:text-gray-50 truncate"
                                >
                                  {member.name}
                                </p>
                                {member.linkedin_url && (
                                  <a
                                    href={member.linkedin_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[#0077B5] hover:text-[#0066a1] transition-colors"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <Linkedin className="w-3.5 h-3.5" />
                                  </a>
                                )}
                              </div>
                              <p
                                className="text-[10px] text-gray-500 truncate"
                
                              >
                                {member.title || "Sem cargo"}
                              </p>
                              {member.email && (
                                <p
                                  className="text-[9px] text-gray-400 truncate"
                                >
                                  {member.email}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>

          <DialogFooter className="mt-4">
            <Button
              variant="outline"
              size="sm"
              className="rounded-md text-[11px]"
              onClick={() => setOrgChartDepartment(null)}
            >
              Fechar
            </Button>
            <Button
              size="sm"
              className="rounded-md text-[11px] bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              onClick={() => {
                if (orgChartDepartment) {
                  handleStartEditDepartment(orgChartDepartment);
                  setOrgChartDepartment(null);
                }
              }}
            >
              <Edit className="w-3.5 h-3.5 mr-1" />
              Editar Departamento
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );

  const renderApprovers = () => (
    <div className="space-y-3">
      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-md p-2 flex items-center gap-2 text-green-700 text-[11px]">
          <CheckCircle className="w-3.5 h-3.5" />
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-2 flex items-center gap-2 text-red-700 text-[11px]">
          <AlertCircle className="w-3.5 h-3.5" />
          {error}
        </div>
      )}

      <Card className="border border-gray-200/50 dark:border-gray-700/50 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle
                className="text-[13px] font-semibold flex items-center gap-2"

              >
                <Crown className="w-3.5 h-3.5 text-gray-500" />
                Fluxo de Aprovação de Vagas
              </CardTitle>
              <p
                className="text-[11px] text-gray-600 mt-1"

              >
                Configure os níveis de aprovação para abertura de vagas
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5 py-1.5 px-2 text-[11px] rounded-full border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              onClick={() => {
                setNewApprover({
                  userName: "",
                  email: "",
                  role: "",
                  level: approvers.length + 1,
                });
                setShowApproverForm(true);
              }}
            >
              <Plus className="w-3.5 h-3.5" />
              Adicionar Nível
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-3 space-y-3">
          {(showApproverForm || editingApprover) && (
            <Card className="border-2 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 rounded-md mb-3">
              <CardContent className="p-3 space-y-2">
                <h4
                  className="text-xs font-semibold"
  
                >
                  {editingApprover ? "Editar Aprovador" : "Novo Aprovador"}
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label
                      className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
      
                    >
                      Nome
                    </label>
                    <input
                      type="text"
                      className="w-full px-2 py-1.5 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs dark:text-gray-100"
                      placeholder="Nome do aprovador"
                      value={
                        editingApprover
                          ? editingApprover.userName
                          : newApprover.userName
                      }
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({
                              ...editingApprover,
                              userName: e.target.value,
                            })
                          : setNewApprover((prev) => ({
                              ...prev,
                              userName: e.target.value,
                            }))
                      }
                    />
                  </div>
                  <div>
                    <label
                      className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
      
                    >
                      Email
                    </label>
                    <input
                      type="email"
                      className="w-full px-2 py-1.5 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs dark:text-gray-100"
                      placeholder="email@empresa.com"
                      value={
                        editingApprover
                          ? editingApprover.email
                          : newApprover.email
                      }
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({
                              ...editingApprover,
                              email: e.target.value,
                            })
                          : setNewApprover((prev) => ({
                              ...prev,
                              email: e.target.value,
                            }))
                      }
                    />
                  </div>
                  <div>
                    <label
                      className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
      
                    >
                      Cargo
                    </label>
                    <input
                      type="text"
                      className="w-full px-2 py-1.5 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs dark:text-gray-100"
                      placeholder="Ex: Gerente de RH"
                      value={
                        editingApprover
                          ? editingApprover.role
                          : newApprover.role
                      }
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({
                              ...editingApprover,
                              role: e.target.value,
                            })
                          : setNewApprover((prev) => ({
                              ...prev,
                              role: e.target.value,
                            }))
                      }
                    />
                  </div>
                  <div>
                    <label
                      className="block text-[10px] font-medium text-gray-600 dark:text-gray-400 mb-1"
      
                    >
                      Nível de Aprovação
                    </label>
                    <input
                      type="number"
                      min="1"
                      className="w-full px-2 py-1.5 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-xs dark:text-gray-100"
                      value={
                        editingApprover
                          ? editingApprover.level
                          : newApprover.level
                      }
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({
                              ...editingApprover,
                              level: parseInt(e.target.value) || 1,
                            })
                          : setNewApprover((prev) => ({
                              ...prev,
                              level: parseInt(e.target.value) || 1,
                            }))
                      }
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowApproverForm(false);
                      setEditingApprover(null);
                    }}
                    className="py-1.5 px-2 text-[11px] rounded-full"
    
                  >
                    Cancelar
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSaveApprover}
                    className="py-1.5 px-2 text-[11px] rounded-full bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                  >
                    <Save className="w-3.5 h-3.5 mr-1" />
                    Salvar
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {approvers.length === 0 && !showApproverForm ? (
            <div className="text-center py-6 text-gray-600">
              <Crown className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p
                className="text-[11px]"

              >
                Nenhum aprovador configurado
              </p>
              <p
                className="text-[10px] mt-1"

              >
                Clique em "Adicionar Nível" para criar um fluxo de aprovação
              </p>
            </div>
          ) : (
            <div className="relative">
              <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />
              {approvers
                .sort((a, b) => a.level - b.level)
                .map((approver, index) => (
                  <div
                    key={approver.id}
                    className="relative flex items-center gap-3 pb-4 last:pb-0"
                  >
                    <div
 className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center text-[11px] font-semibold ${approver.isActive ? "text-white" : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"}`}
                    >
                      {approver.level}
                    </div>
                    <Card className="flex-1 border border-gray-200/50 dark:border-gray-700/50 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-md">
                      <CardContent className="p-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback
                              className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-[10px]"
              
                            >
                              {approver.userName
                                .split(" ")
                                .map((n) => n[0])
                                .join("")}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-[11px] font-semibold text-gray-950 dark:text-gray-50">
                              {approver.userName}
                            </p>
                            <p
                              className="text-[10px] text-gray-600"
              
                            >
                              {approver.role} • {approver.email}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Badge
                            variant={approver.isActive ? "default" : "outline"}
                            className={`text-[10px] rounded-md ${
                              approver.isActive
                                ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                : "border-gray-200 dark:border-gray-700"
                            }`}
                          >
                            {approver.isActive ? "Ativo" : "Inativo"}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                            onClick={() => setEditingApprover(approver)}
                          >
                            <Edit className="w-3.5 h-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 rounded-md text-red-500 hover:text-red-600 hover:bg-red-50"
                            onClick={() => handleDeleteApprover(approver.id)}
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                ))}
            </div>
          )}

          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-2 border border-gray-200 dark:border-gray-700">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-gray-500" />
              <div>
                <p className="text-[11px] font-semibold text-gray-700 dark:text-gray-300">
                  Fluxo de Aprovação
                </p>
                <p className="text-[10px] mt-0.5 text-gray-600 dark:text-gray-400">
                  Vagas serão enviadas para aprovação sequencial, do nível 1 ao
                  nível final. Cada aprovador receberá notificação por email e
                  pode aprovar diretamente na plataforma.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderUsers = () => <UserManagement onUserUpdate={onUserUpdate} />;

  const EmptyFieldWarning = ({ fieldName }: { fieldName: string }) => (
    <div className="flex items-center gap-1.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-200/50 dark:border-amber-700/30 rounded-md px-2 py-1">
      <AlertCircle className="w-3 h-3 text-amber-500 flex-shrink-0" />
      <span
        className="text-[10px] text-amber-600 dark:text-amber-400"
      >
        Não informado - preencher manualmente
      </span>
    </div>
  );


  const renderTechStack = () => {
    return (
      <Card className={cardStyles.default}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
              <Code className="w-4 h-4" />
              Tech Stack por Categoria
            </CardTitle>
            <div className="flex items-center gap-2">
              <LiaFieldToggle
                fieldKey="tech_stack"
                isActive={companyData.lia_field_toggles?.tech_stack ?? true}
                currentInstruction={companyData.lia_instructions?.tech_stack || ''}
                examples={defaultLiaFieldExamples.tech_stack}
                onToggleChange={updateLiaToggle}
                onInstructionSave={updateLiaInstruction}
                compact
              />
              {!isEditingCompanyData ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditingCompanyData(true)}
                  className="h-7 text-[11px]"
                >
                  <Edit className="w-3 h-3 mr-1" />
                  Editar
                </Button>
              ) : (
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditingCompanyData(false)}
                    className="h-7 text-[11px]"
                  >
                    <X className="w-3 h-3 mr-1" />
                    Cancelar
                  </Button>
                  <Button
                    size="sm"
                    onClick={saveCompanyData}
                    disabled={saving}
                    className="h-7 text-[11px] bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                  >
                    <Save className="w-3 h-3 mr-1" />
                    {saving ? 'Salvando...' : 'Salvar'}
                  </Button>
                </div>
              )}
            </div>
          </div>
          <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-1">
            Configure as tecnologias utilizadas pela empresa por categoria
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {TECH_STACK_CATEGORIES.map((category) => {
            const CategoryIcon = category.icon;
            const isExpanded = expandedCategories[category.key] ?? false;
            const categoryTechs = techStackByCategory[category.key] || [];

            return (
              <div
                key={category.key}
                className="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() =>
                    setExpandedCategories((prev) => ({
                      ...prev,
                      [category.key]: !isExpanded,
                    }))
                  }
                  className={`w-full flex items-center justify-between px-3 py-2.5 ${category.color} hover:opacity-90 transition-opacity`}
                >
                  <div className="flex items-center gap-2">
                    <CategoryIcon className="w-4 h-4" />
                    <span className="text-xs font-medium">
                      {category.label}
                    </span>
                    {categoryTechs.length > 0 && (
                      <Badge className="bg-white/50 dark:bg-black/20 text-[10px] px-1.5 py-0.5">
                        {categoryTechs.length}
                      </Badge>
                    )}
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>

                {isExpanded && (
                  <div className="p-3 bg-white dark:bg-gray-800 space-y-3">
                    {categoryTechs.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {categoryTechs.map((tech, idx) => (
                          <Badge
                            key={idx}
                            className={`${category.color} text-[11px] px-2.5 py-1 rounded-full`}
                          >
                            {tech}
                            {isEditingCompanyData && (
                              <button
                                onClick={() =>
                                  removeTechFromCategory(category.key, tech)
                                }
                                className="ml-1.5 hover:text-red-500"
                              >
                                ×
                              </button>
                            )}
                          </Badge>
                        ))}
                      </div>
                    )}

                    <div className="flex flex-wrap gap-1.5">
                      {category.suggestions
                        .filter((s) => !categoryTechs.includes(s))
                        .slice(0, 8)
                        .map((suggestion) => (
                          <button
                            key={suggestion}
                            type="button"
                            disabled={!isEditingCompanyData}
                            onClick={() => {
                              if (!isEditingCompanyData) return;
                              addTechToCategory(category.key, suggestion);
                            }}
                            className={`text-[10px] px-2 py-1 border border-dashed border-gray-300 dark:border-gray-600 rounded-full text-gray-500 dark:text-gray-400 hover:border-gray-400 hover:text-gray-700 dark:hover:border-gray-500 dark:hover:text-gray-300 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                          >
                            + {suggestion}
                          </button>
                        ))}
                    </div>

                    <input
                      type="text"
                      placeholder={`Adicionar ${category.label.toLowerCase()} personalizada...`}
                      disabled={!isEditingCompanyData}
                      className={`w-full px-3 py-2 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && e.currentTarget.value.trim()) {
                          e.preventDefault();
                          addTechToCategory(category.key, e.currentTarget.value.trim());
                          e.currentTarget.value = "";
                        }
                      }}
                    />
                  </div>
                )}
              </div>
            );
          })}

          {techStackByCategory["outros"] && techStackByCategory["outros"].length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
              <button
                type="button"
                onClick={() =>
                  setExpandedCategories((prev) => ({
                    ...prev,
                    outros: !prev.outros,
                  }))
                }
                className="w-full flex items-center justify-between px-3 py-2.5 bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 hover:opacity-90 transition-opacity"
              >
                <div className="flex items-center gap-2">
                  <Code className="w-4 h-4" />
                  <span className="text-xs font-medium">Outros</span>
                  <Badge className="bg-white/50 dark:bg-black/20 text-[10px] px-1.5 py-0.5">
                    {techStackByCategory["outros"].length}
                  </Badge>
                </div>
                {expandedCategories.outros ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>

              {expandedCategories.outros && (
                <div className="p-3 bg-white dark:bg-gray-800 space-y-3">
                  <div className="flex flex-wrap gap-1.5">
                    {techStackByCategory["outros"].map((tech, idx) => (
                      <Badge
                        key={idx}
                        className="bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-[11px] px-2.5 py-1 rounded-full"
                      >
                        {tech}
                        {isEditingCompanyData && (
                          <button
                            onClick={() => removeTechFromCategory("outros", tech)}
                            className="ml-1.5 hover:text-red-500"
                          >
                            ×
                          </button>
                        )}
                      </Badge>
                    ))}
                  </div>

                  <input
                    type="text"
                    placeholder="Adicionar tecnologia..."
                    disabled={!isEditingCompanyData}
                    className={`w-full px-3 py-2 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-900 focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed' : ''}`}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && e.currentTarget.value.trim()) {
                        e.preventDefault();
                        addTechToCategory("outros", e.currentTarget.value.trim());
                        e.currentTarget.value = "";
                      }
                    }}
                  />
                </div>
              )}
            </div>
          )}

          <div className="border-t border-gray-100 dark:border-gray-800 pt-4">
            <label className="flex items-center gap-3 text-[11px] font-medium text-gray-600 dark:text-gray-400 mb-2">
              <span className="flex items-center gap-1">
                <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                Cultura de Engenharia
              </span>
              <LiaFieldToggle
                fieldKey="engineering_culture"
                isActive={companyData.lia_field_toggles?.engineering_culture ?? true}
                currentInstruction={companyData.lia_instructions?.engineering_culture || ''}
                examples={defaultLiaFieldExamples.engineering_culture}
                onToggleChange={updateLiaToggle}
                onInstructionSave={updateLiaInstruction}
                compact
              />
            </label>
            <textarea
              value={companyData.engineering_culture || ""}
              disabled={!isEditingCompanyData}
              onChange={(e) =>
                setCompanyData((prev) => ({
                  ...prev,
                  engineering_culture: e.target.value,
                }))
              }
 className={`w-full px-3 py-2 text-xs border border-gray-200 dark:border-gray-700 rounded-md bg-white focus:ring-2 focus:ring-gray-200 focus:border-gray-400 dark:focus:ring-gray-700 dark:focus:border-gray-500 transition-colors ${!isEditingCompanyData ? 'opacity-60 cursor-not-allowed bg-gray-50 dark:bg-gray-900' : ''}`}
              rows={3}
              placeholder="Descreva a cultura de engenharia da empresa (metodologias, práticas de desenvolvimento, ambiente de trabalho técnico)..."
            />
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderContent = () => {
    switch (activeTab) {
      case "company-data":
        return renderCompanyData();
      case "departments":
        return renderDepartments();
      case "tech-stack":
        return renderTechStack();
      case "benefits":
        return <BenefitsTab />;
      case "users":
        return renderUsers();
      default:
        return renderCompanyData();
    }
  };

  return (
    <div className="space-y-3">
      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>

      {renderContent()}
    </div>
  );
}
