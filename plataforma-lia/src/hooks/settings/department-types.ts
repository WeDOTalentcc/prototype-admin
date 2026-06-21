export interface Department {
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

export interface DepartmentMember {
  id: string;
  name: string;
  title?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  avatar_url?: string;
  level: string;
  is_active: boolean;
  // B1 (2026-05-25): backend FK to users.id
  user_id?: string | null;
}

export interface Approver {
  id: string;
  userId: string;
  userName: string;
  email: string;
  role: string;
  level: number;
  isActive: boolean;
  // P0.D2 (audit Wave 2 2026-05-22): per-department + amount-threshold routing.
  // Both null = backward-compat (company-wide, any-amount approver).
  departmentId: string | null;
  canApproveAboveAmount: number | null;
}

export interface BehavioralCompetency {
  competency: string;
  weight: "Essencial" | "Importante" | "Desejável";
}

export interface SalaryRange {
  department?: string;
  level: string;
  min: number;
  max: number;
  currency: string;
}

export interface LiaInstructions {
  [fieldKey: string]: string;
}

export interface LiaFieldToggles {
  [fieldKey: string]: boolean;
}

export interface CompanyData {
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

export interface CompanyTeamHubProps {
  activeSubsection?: string;
  onUserUpdate?: (user: import('@/components/settings/user-management-types').UserData) => void;
  onGoalUpdate?: (userId: string, goals: Record<string, unknown>) => void;
}

export type TechStackByCategory = Record<string, string[]>;

export interface NewDepartmentForm {
  name: string;
  description: string;
  manager: string;
  manager_title: string;
  manager_email: string;
  manager_phone: string;
  color: string;
}

export interface NewMemberForm {
  name: string;
  title: string;
  email: string;
  phone: string;
  linkedin_url: string;
  level: string;
  // B1 (2026-05-25): optional FK to users.id (platform user) | null = external contact
  user_id?: string | null;
}

export interface NewApproverForm {
  userName: string;
  email: string;
  role: string;
  level: number;
  departmentId: string | null;
  canApproveAboveAmount: number | null;
  // Sprint 2 (2026-06-21): TIPO A = user from platform; TIPO B = external magic link
  userId?: string | null;
  approvalMethod: "platform" | "email_link";
}

export const DEFAULT_NEW_DEPARTMENT: NewDepartmentForm = {
  name: "",
  description: "",
  manager: "",
  manager_title: "",
  manager_email: "",
  manager_phone: "",
  color: "bg-lia-btn-primary-bg text-lia-btn-primary-text",
};

export const DEFAULT_NEW_MEMBER: NewMemberForm = {
  name: "",
  title: "",
  email: "",
  phone: "",
  linkedin_url: "",
  level: "outros",
  user_id: null,
};

export const COLOR_OPTIONS = [
  "bg-lia-btn-primary-bg text-lia-btn-primary-text",
  "bg-wedo-green text-white",
  "bg-wedo-orange text-white",
  "bg-wedo-purple text-white",
  "bg-wedo-magenta text-white",
  "bg-wedo-cyan text-white",
  "bg-status-error text-white",
  "bg-status-warning text-white",
];

export const defaultCompanyData: CompanyData = {
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

import {
  Server,
  Layout,
  Database,
  Cloud,
  Settings,
  Brain,
  Briefcase,
  Palette,
  Smartphone,
} from "lucide-react";

export const TECH_STACK_CATEGORIES = [
  {
    key: "backend",
    label: "Backend",
    icon: Server,
    color: "bg-lia-bg-tertiary text-lia-text-primary",
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
      "bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success",
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
      "bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning",
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
    color: "bg-wedo-cyan/10 text-wedo-cyan-text dark:bg-wedo-cyan/20 dark:text-wedo-cyan-dark",
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
      "bg-wedo-purple/10 text-wedo-purple-text dark:bg-wedo-purple/20 dark:text-wedo-purple",
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
    color: "bg-wedo-magenta/10 text-wedo-magenta-text dark:bg-wedo-magenta/20 dark:text-wedo-magenta",
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
      "bg-wedo-orange/10 text-wedo-orange-text dark:bg-wedo-orange/20 dark:text-wedo-orange",
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
    color: "bg-wedo-magenta/10 text-wedo-magenta-text dark:bg-wedo-magenta/20 dark:text-wedo-magenta",
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
      "bg-wedo-purple/10 text-wedo-purple-text dark:bg-wedo-purple/20 dark:text-wedo-purple",
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

export const parseTechStackToCategories = (
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

export const categoriesToTechStack = (categories: TechStackByCategory): string[] => {
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

export const getLevelOrder = (level: string): number => {
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

export const getLevelLabel = (level: string): string => {
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

export const getLevelColor = (level: string): string => {
  const colors: Record<string, string> = {
    ceo: "bg-lia-btn-primary-bg text-lia-btn-primary-text border-lia-border-strong dark:border-lia-border-subtle",
    vp: "bg-lia-btn-primary-hover text-white border-lia-border-strong dark:border-lia-border-default",
    diretor: "bg-lia-bg-inverse text-white border-lia-border-medium dark:border-lia-border-medium",
    gerente_senior: "bg-lia-border-medium text-white border-lia-border-medium dark:border-lia-border-medium",
    gerente: "bg-lia-bg-secondary0 text-white border-lia-border-medium dark:text-white dark:border-lia-border-medium",
    lider: "bg-lia-border-medium text-lia-text-primary border-lia-border-default dark:text-white dark:border-lia-border-strong",
    supervisor: "bg-lia-border-default text-lia-text-primary border-lia-border-subtle dark:border-lia-border-strong",
    especialista: "bg-lia-interactive-active text-lia-text-primary border-lia-border-subtle dark:border-lia-btn-primary-bg",
    analista: "bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle dark:border-lia-border-strong",
    estagiario: "bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle dark:border-lia-border-strong",
    outros: "bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle dark:border-lia-border-strong",
  };
  return colors[level] || "bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle dark:border-lia-border-strong";
};
