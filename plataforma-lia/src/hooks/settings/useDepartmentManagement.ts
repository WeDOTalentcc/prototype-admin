import { useReducer, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  type Department,
  type DepartmentMember,
  type Approver,
  type NewDepartmentForm,
  type NewMemberForm,
  type NewApproverForm,
  DEFAULT_NEW_DEPARTMENT,
  DEFAULT_NEW_MEMBER,
} from "@/hooks/settings/department-types";
import { useCompanyId } from "@/hooks/company/useCompanyId";
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify";
import { toast } from "@/lib/toast";

// ─── Public interfaces (backward-compatible) ─────────────────────────────────

export interface UseDepartmentManagementState {
  departments: Department[];
  editingDepartment: Department | null;
  showDepartmentForm: boolean;
  departmentToDelete: Department | null;
  newDepartment: NewDepartmentForm;
  isEditingDepartments: boolean;
  departmentsBackup: Department[];
  departmentMembers: DepartmentMember[];
  showMemberForm: boolean;
  editingMember: DepartmentMember | null;
  savingMember: boolean;
  memberError: string | null;
  memberSuccess: string | null;
  newMember: NewMemberForm;
  orgChartDepartment: Department | null;
  orgChartMembers: DepartmentMember[];
  loadingOrgChart: boolean;
  approvers: Approver[];
  showApproverForm: boolean;
  editingApprover: Approver | null;
  newApprover: NewApproverForm;
}

export interface UseDepartmentManagementActions {
  setDepartments: (depts: Department[] | ((prev: Department[]) => Department[])) => void;
  setEditingDepartment: (dept: Department | null) => void;
  setShowDepartmentForm: (show: boolean) => void;
  setDepartmentToDelete: (dept: Department | null) => void;
  setNewDepartment: (form: NewDepartmentForm | ((prev: NewDepartmentForm) => NewDepartmentForm)) => void;
  setIsEditingDepartments: (editing: boolean) => void;
  setDepartmentsBackup: (backup: Department[]) => void;
  setShowMemberForm: (show: boolean) => void;
  setEditingMember: (member: DepartmentMember | null) => void;
  setNewMember: (form: NewMemberForm | ((prev: NewMemberForm) => NewMemberForm)) => void;
  setMemberError: (error: string | null) => void;
  setOrgChartDepartment: (dept: Department | null) => void;
  setApprovers: (approvers: Approver[] | ((prev: Approver[]) => Approver[])) => void;
  setShowApproverForm: (show: boolean) => void;
  setEditingApprover: (approver: Approver | null) => void;
  setNewApprover: (form: NewApproverForm | ((prev: NewApproverForm) => NewApproverForm)) => void;
  loadDepartments: () => Promise<void>;
  handleSaveDepartment: () => Promise<void>;
  handleDeleteDepartment: (id: string) => Promise<void>;
  handleStartEditDepartment: (dept: Department) => void;
  handleCancelDepartmentForm: () => void;
  handleSaveMember: () => Promise<void>;
  handleEditMember: (member: DepartmentMember) => void;
  handleDeleteMember: (memberId: string) => Promise<void>;
  handleOpenOrgChart: (dept: Department) => Promise<void>;
  handleSaveApprover: () => Promise<void>;
  handleDeleteApprover: (id: string) => Promise<void>;
}

export interface UseDepartmentManagementResult {
  state: UseDepartmentManagementState;
  actions: UseDepartmentManagementActions;
}

interface UseDepartmentManagementOptions {
  initialDepartments: Department[];
  initialApprovers: Approver[];
  setError: (error: string | null) => void;
  setSuccessMessage: (message: string | null) => void;
}

// ─── UI state managed via useReducer ─────────────────────────────────────────

interface UIState {
  // Department form
  editingDepartment: Department | null;
  showDepartmentForm: boolean;
  departmentToDelete: Department | null;
  newDepartment: NewDepartmentForm;
  isEditingDepartments: boolean;
  departmentsBackup: Department[];
  // Departments override (when mutations return data or initial props arrive)
  departmentsOverride: Department[] | null;
  // Member
  departmentMembers: DepartmentMember[];
  showMemberForm: boolean;
  editingMember: DepartmentMember | null;
  savingMember: boolean;
  memberError: string | null;
  memberSuccess: string | null;
  newMember: NewMemberForm;
  // Org chart
  orgChartDepartment: Department | null;
  orgChartMembers: DepartmentMember[];
  loadingOrgChart: boolean;
  // Approvers override
  approversOverride: Approver[] | null;
  // Approver form
  showApproverForm: boolean;
  editingApprover: Approver | null;
  newApprover: NewApproverForm;
}

type UIAction =
  | { type: "SET_EDITING_DEPT"; payload: Department | null }
  | { type: "SET_SHOW_DEPT_FORM"; payload: boolean }
  | { type: "SET_DEPT_TO_DELETE"; payload: Department | null }
  | { type: "SET_NEW_DEPT"; payload: NewDepartmentForm | ((prev: NewDepartmentForm) => NewDepartmentForm) }
  | { type: "SET_IS_EDITING_DEPTS"; payload: boolean }
  | { type: "SET_DEPTS_BACKUP"; payload: Department[] }
  | { type: "SET_DEPTS_OVERRIDE"; payload: Department[] | ((prev: Department[] | null) => Department[] | null) }
  | { type: "SET_DEPT_MEMBERS"; payload: DepartmentMember[] }
  | { type: "SET_SHOW_MEMBER_FORM"; payload: boolean }
  | { type: "SET_EDITING_MEMBER"; payload: DepartmentMember | null }
  | { type: "SET_SAVING_MEMBER"; payload: boolean }
  | { type: "SET_MEMBER_ERROR"; payload: string | null }
  | { type: "SET_MEMBER_SUCCESS"; payload: string | null }
  | { type: "SET_NEW_MEMBER"; payload: NewMemberForm | ((prev: NewMemberForm) => NewMemberForm) }
  | { type: "SET_ORG_CHART_DEPT"; payload: Department | null }
  | { type: "SET_ORG_CHART_MEMBERS"; payload: DepartmentMember[] }
  | { type: "SET_LOADING_ORG_CHART"; payload: boolean }
  | { type: "SET_APPROVERS_OVERRIDE"; payload: Approver[] | ((prev: Approver[] | null) => Approver[] | null) }
  | { type: "SET_SHOW_APPROVER_FORM"; payload: boolean }
  | { type: "SET_EDITING_APPROVER"; payload: Approver | null }
  | { type: "SET_NEW_APPROVER"; payload: NewApproverForm | ((prev: NewApproverForm) => NewApproverForm) };

const DEFAULT_NEW_APPROVER: NewApproverForm = {
  userName: "",
  email: "",
  role: "",
  level: 1,
  departmentId: null,
  canApproveAboveAmount: null,
};

const initialUIState: UIState = {
  editingDepartment: null,
  showDepartmentForm: false,
  departmentToDelete: null,
  newDepartment: { ...DEFAULT_NEW_DEPARTMENT },
  isEditingDepartments: false,
  departmentsBackup: [],
  departmentsOverride: null,
  departmentMembers: [],
  showMemberForm: false,
  editingMember: null,
  savingMember: false,
  memberError: null,
  memberSuccess: null,
  newMember: { ...DEFAULT_NEW_MEMBER },
  orgChartDepartment: null,
  orgChartMembers: [],
  loadingOrgChart: false,
  approversOverride: null,
  showApproverForm: false,
  editingApprover: null,
  newApprover: { ...DEFAULT_NEW_APPROVER },
};

function uiReducer(state: UIState, action: UIAction): UIState {
  switch (action.type) {
    case "SET_EDITING_DEPT":
      return { ...state, editingDepartment: action.payload };
    case "SET_SHOW_DEPT_FORM":
      return { ...state, showDepartmentForm: action.payload };
    case "SET_DEPT_TO_DELETE":
      return { ...state, departmentToDelete: action.payload };
    case "SET_NEW_DEPT":
      return {
        ...state,
        newDepartment: typeof action.payload === "function"
          ? action.payload(state.newDepartment)
          : action.payload,
      };
    case "SET_IS_EDITING_DEPTS":
      return { ...state, isEditingDepartments: action.payload };
    case "SET_DEPTS_BACKUP":
      return { ...state, departmentsBackup: action.payload };
    case "SET_DEPTS_OVERRIDE":
      return {
        ...state,
        departmentsOverride: typeof action.payload === "function"
          ? action.payload(state.departmentsOverride)
          : action.payload,
      };
    case "SET_DEPT_MEMBERS":
      return { ...state, departmentMembers: action.payload };
    case "SET_SHOW_MEMBER_FORM":
      return { ...state, showMemberForm: action.payload };
    case "SET_EDITING_MEMBER":
      return { ...state, editingMember: action.payload };
    case "SET_SAVING_MEMBER":
      return { ...state, savingMember: action.payload };
    case "SET_MEMBER_ERROR":
      return { ...state, memberError: action.payload };
    case "SET_MEMBER_SUCCESS":
      return { ...state, memberSuccess: action.payload };
    case "SET_NEW_MEMBER":
      return {
        ...state,
        newMember: typeof action.payload === "function"
          ? action.payload(state.newMember)
          : action.payload,
      };
    case "SET_ORG_CHART_DEPT":
      return { ...state, orgChartDepartment: action.payload };
    case "SET_ORG_CHART_MEMBERS":
      return { ...state, orgChartMembers: action.payload };
    case "SET_LOADING_ORG_CHART":
      return { ...state, loadingOrgChart: action.payload };
    case "SET_APPROVERS_OVERRIDE":
      return {
        ...state,
        approversOverride: typeof action.payload === "function"
          ? action.payload(state.approversOverride)
          : action.payload,
      };
    case "SET_SHOW_APPROVER_FORM":
      return { ...state, showApproverForm: action.payload };
    case "SET_EDITING_APPROVER":
      return { ...state, editingApprover: action.payload };
    case "SET_NEW_APPROVER":
      return {
        ...state,
        newApprover: typeof action.payload === "function"
          ? action.payload(state.newApprover)
          : action.payload,
      };
    default:
      return state;
  }
}

// ─── API helpers ──────────────────────────────────────────────────────────────

function mapDepartmentFromApi(d: {
  id: string;
  name: string;
  description?: string;
  manager_name?: string;
  manager_title?: string;
  manager_email?: string;
  manager_phone?: string;
  headcount?: number;
  color?: string;
}): Department {
  return {
    id: d.id,
    name: d.name,
    description: d.description || "",
    manager: d.manager_name || undefined,
    manager_title: d.manager_title || undefined,
    manager_email: d.manager_email || undefined,
    manager_phone: d.manager_phone || undefined,
    headcount: d.headcount || 0,
    color: d.color || "bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary",
  };
}

async function fetchDepartments(companyId?: string): Promise<Department[]> {
  const url = companyId
    ? `/api/backend-proxy/company/departments?company_id=${encodeURIComponent(companyId)}`
    : "/api/backend-proxy/company/departments";
  const res = await fetch(url);
  if (!res.ok) throw new Error("Falha ao carregar departamentos");
  const data = await res.json();
  return Array.isArray(data) ? data.map(mapDepartmentFromApi) : [];
}

async function fetchDepartmentMembers(departmentId: string): Promise<DepartmentMember[]> {
  const res = await fetch(`/api/backend-proxy/company/departments/${departmentId}/members`);
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useDepartmentManagement({
  initialDepartments,
  initialApprovers,
  setError,
  setSuccessMessage,
}: UseDepartmentManagementOptions): UseDepartmentManagementResult {
  const { companyId } = useCompanyId();
  const queryClient = useQueryClient();
  const [ui, dispatch] = useReducer(uiReducer, initialUIState);

  const isMountedRef = useRef(true);
  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);

  // ── React Query: departments list ──────────────────────────────────────────
  const { data: queriedDepartments = [] } = useQuery<Department[]>({
    queryKey: ["departments", companyId],
    queryFn: () => fetchDepartments(companyId),
    staleTime: 30_000,
    initialData: initialDepartments.length > 0 ? initialDepartments : undefined,
  });

  // Merge: override (optimistic/loaded) takes precedence, else query result
  const departments: Department[] = ui.departmentsOverride ?? queriedDepartments;
  const approvers: Approver[] = ui.approversOverride ?? initialApprovers;

  // Sync initialDepartments prop changes into override only when needed
  useEffect(() => {
    if (initialDepartments.length > 0 && ui.departmentsOverride === null) {
      dispatch({ type: "SET_DEPTS_OVERRIDE", payload: initialDepartments });
    }
  }, [initialDepartments]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (initialApprovers.length > 0 && ui.approversOverride === null) {
      dispatch({ type: "SET_APPROVERS_OVERRIDE", payload: initialApprovers });
    }
  }, [initialApprovers]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Mutation: save department ──────────────────────────────────────────────
  const saveDeptMutation = useMutation({
    mutationFn: async ({ dept, isNew }: { dept: Department; isNew: boolean }) => {
      const method = isNew ? "POST" : "PUT";
      const url = isNew
        ? `/api/backend-proxy/company/departments?company_id=${encodeURIComponent(companyId || "")}`
        : `/api/backend-proxy/company/departments/${dept.id}`;
      const res = await fetch(url, {
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
      if (!res.ok) throw new Error("Falha ao salvar departamento");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["departments"] });
    },
  });

  // ── Mutation: delete department ────────────────────────────────────────────
  const deleteDeptMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/backend-proxy/company/departments/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Falha ao remover departamento");
      notifyChatOfSettingsUpdate({ actionId: "delete_department", section: "departments", field: id });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["departments"] });
    },
  });

  // ── Mutation: save approver ────────────────────────────────────────────────
  const saveApproverMutation = useMutation({
    mutationFn: async ({
      approver,
      isNew,
      id,
    }: {
      approver: {
        userName: string;
        email: string;
        role: string;
        level: number;
        departmentId: string | null;
        canApproveAboveAmount: number | null;
      };
      isNew: boolean;
      id?: string;
    }) => {
      const method = isNew ? "POST" : "PUT";
      const url = isNew
        ? `/api/backend-proxy/company/approvers?company_id=${encodeURIComponent(companyId || "")}`
        : `/api/backend-proxy/company/approvers/${id}`;
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_name: approver.userName,
          email: approver.email,
          role: approver.role,
          level: approver.level,
          department_id: approver.departmentId,
          can_approve_above_amount: approver.canApproveAboveAmount,
        }),
      });
      if (!res.ok) throw new Error("Falha ao salvar aprovador");
      return res.json();
    },
  });

  // ── Mutation: delete approver ──────────────────────────────────────────────
  const deleteApproverMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/backend-proxy/company/approvers/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Falha ao remover aprovador");
      notifyChatOfSettingsUpdate({ actionId: "delete_approver", section: "departments", field: id });
    },
  });

  // ── Mutation: save member ──────────────────────────────────────────────────
  const saveMemberMutation = useMutation({
    mutationFn: async ({
      member,
      departmentId,
      editingMemberId,
    }: {
      member: NewMemberForm;
      departmentId: string;
      editingMemberId?: string;
    }) => {
      const url = editingMemberId
        ? `/api/backend-proxy/company/members/${editingMemberId}`
        : `/api/backend-proxy/company/departments/${departmentId}/members`;
      const method = editingMemberId ? "PUT" : "POST";
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(member),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || "Erro ao salvar colaborador");
      }
      return res.json();
    },
  });

  // ── Mutation: delete member ────────────────────────────────────────────────
  const deleteMemberMutation = useMutation({
    mutationFn: async (memberId: string) => {
      const res = await fetch(`/api/backend-proxy/company/members/${memberId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Falha ao remover colaborador");
      notifyChatOfSettingsUpdate({ actionId: "delete_department_member", section: "departments", field: memberId });
    },
  });

  // ── Helpers ────────────────────────────────────────────────────────────────

  function flashSuccess(msg: string) {
    setSuccessMessage(msg);
    setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000);
  }

  function flashError(msg: string) {
    setError(msg);
    setTimeout(() => { if (isMountedRef.current) setError(null); }, 3000);
  }

  async function loadDepartmentMembers(departmentId: string) {
    const members = await fetchDepartmentMembers(departmentId);
    dispatch({ type: "SET_DEPT_MEMBERS", payload: members });
  }

  // ── Public actions ─────────────────────────────────────────────────────────

  async function loadDepartments() {
    try {
      const data = await fetchDepartments(companyId);
      dispatch({ type: "SET_DEPTS_OVERRIDE", payload: data });
    } catch (err) {
      console.error("[Departments] loadDepartments failed:", err);
      toast.error("Falha ao carregar departamentos. Tente novamente.", "Verifique sua conexão e tente novamente.");
    }
  }

  async function handleSaveDepartment() {
    if (!ui.newDepartment.name) return;

    if (ui.editingDepartment) {
      const updatedDept: Department = {
        ...ui.editingDepartment,
        name: ui.newDepartment.name,
        description: ui.newDepartment.description,
        manager: ui.newDepartment.manager,
        manager_title: ui.newDepartment.manager_title,
        manager_email: ui.newDepartment.manager_email,
        manager_phone: ui.newDepartment.manager_phone,
        color: ui.newDepartment.color,
      };
      try {
        await saveDeptMutation.mutateAsync({ dept: updatedDept, isNew: false });
        dispatch({
          type: "SET_DEPTS_OVERRIDE",
          payload: (prev) => (prev ?? departments).map((d) => (d.id === updatedDept.id ? updatedDept : d)),
        });
        flashSuccess("Departamento atualizado com sucesso!");
      } catch {
        flashError("Erro ao atualizar departamento");
      }
      dispatch({ type: "SET_EDITING_DEPT", payload: null });
      dispatch({ type: "SET_NEW_DEPT", payload: { ...DEFAULT_NEW_DEPARTMENT } });
      dispatch({ type: "SET_SHOW_DEPT_FORM", payload: false });
      dispatch({ type: "SET_DEPT_MEMBERS", payload: [] });
      dispatch({ type: "SET_SHOW_MEMBER_FORM", payload: false });
    } else {
      const dept: Department = {
        id: `dept-${Date.now()}`,
        name: ui.newDepartment.name,
        description: ui.newDepartment.description,
        manager: ui.newDepartment.manager,
        manager_title: ui.newDepartment.manager_title,
        manager_email: ui.newDepartment.manager_email,
        manager_phone: ui.newDepartment.manager_phone,
        headcount: 0,
        color: ui.newDepartment.color,
      };
      try {
        const result = await saveDeptMutation.mutateAsync({ dept, isNew: true });
        if (result?.id) dept.id = result.id;
        dispatch({ type: "SET_DEPTS_OVERRIDE", payload: [...departments, dept] });
        flashSuccess("Departamento criado com sucesso!");
      } catch {
        dispatch({ type: "SET_DEPTS_OVERRIDE", payload: [...departments, dept] });
      }
      dispatch({ type: "SET_NEW_DEPT", payload: { ...DEFAULT_NEW_DEPARTMENT } });
      dispatch({ type: "SET_SHOW_DEPT_FORM", payload: false });
    }
  }

  async function handleDeleteDepartment(id: string) {
    dispatch({ type: "SET_DEPTS_OVERRIDE", payload: departments.filter((d) => d.id !== id) });
    try {
      await deleteDeptMutation.mutateAsync(id);
      flashSuccess("Departamento removido com sucesso!");
    } catch {
      flashError("Erro ao remover departamento");
    }
    dispatch({ type: "SET_DEPT_TO_DELETE", payload: null });
  }

  function handleStartEditDepartment(dept: Department) {
    dispatch({ type: "SET_EDITING_DEPT", payload: dept });
    dispatch({
      type: "SET_NEW_DEPT",
      payload: {
        name: dept.name,
        description: dept.description,
        manager: dept.manager || "",
        manager_title: dept.manager_title || "",
        manager_email: dept.manager_email || "",
        manager_phone: dept.manager_phone || "",
        color: dept.color,
      },
    });
    dispatch({ type: "SET_SHOW_DEPT_FORM", payload: true });
    loadDepartmentMembers(dept.id);
  }

  function handleCancelDepartmentForm() {
    dispatch({ type: "SET_SHOW_DEPT_FORM", payload: false });
    dispatch({ type: "SET_EDITING_DEPT", payload: null });
    dispatch({ type: "SET_NEW_DEPT", payload: { ...DEFAULT_NEW_DEPARTMENT } });
    dispatch({ type: "SET_DEPT_MEMBERS", payload: [] });
    dispatch({ type: "SET_SHOW_MEMBER_FORM", payload: false });
    dispatch({ type: "SET_EDITING_MEMBER", payload: null });
    dispatch({ type: "SET_NEW_MEMBER", payload: { ...DEFAULT_NEW_MEMBER } });
  }

  async function handleSaveMember() {
    if (!ui.editingDepartment || !ui.newMember.name) {
      dispatch({ type: "SET_MEMBER_ERROR", payload: "Nome do colaborador é obrigatório" });
      return;
    }
    dispatch({ type: "SET_SAVING_MEMBER", payload: true });
    dispatch({ type: "SET_MEMBER_ERROR", payload: null });
    dispatch({ type: "SET_MEMBER_SUCCESS", payload: null });
    try {
      await saveMemberMutation.mutateAsync({
        member: ui.newMember,
        departmentId: ui.editingDepartment.id,
        editingMemberId: ui.editingMember?.id,
      });
      await loadDepartmentMembers(ui.editingDepartment.id);
      dispatch({ type: "SET_NEW_MEMBER", payload: { ...DEFAULT_NEW_MEMBER } });
      dispatch({ type: "SET_SHOW_MEMBER_FORM", payload: false });
      dispatch({ type: "SET_EDITING_MEMBER", payload: null });
      dispatch({
        type: "SET_MEMBER_SUCCESS",
        payload: ui.editingMember
          ? "Colaborador atualizado com sucesso!"
          : "Colaborador adicionado com sucesso!",
      });
      setTimeout(() => { if (isMountedRef.current) dispatch({ type: "SET_MEMBER_SUCCESS", payload: null }); }, 3000);
    } catch (err) {
      dispatch({ type: "SET_MEMBER_ERROR", payload: err instanceof Error ? err.message : "Erro ao salvar colaborador" });
    } finally {
      dispatch({ type: "SET_SAVING_MEMBER", payload: false });
    }
  }

  function handleEditMember(member: DepartmentMember) {
    dispatch({ type: "SET_EDITING_MEMBER", payload: member });
    dispatch({
      type: "SET_NEW_MEMBER",
      payload: {
        name: member.name,
        title: member.title || "",
        email: member.email || "",
        phone: member.phone || "",
        linkedin_url: member.linkedin_url || "",
        level: member.level || "outros",
      },
    });
    dispatch({ type: "SET_SHOW_MEMBER_FORM", payload: true });
  }

  async function handleDeleteMember(memberId: string) {
    try {
      await deleteMemberMutation.mutateAsync(memberId);
      if (ui.editingDepartment) {
        await loadDepartmentMembers(ui.editingDepartment.id);
      }
    } catch (err) {
      console.error("[Departments] handleDeleteMember failed:", err);
      toast.error("Falha ao remover membro. Tente novamente.", "Verifique sua conexão e tente novamente.");
    }
  }

  async function handleOpenOrgChart(dept: Department) {
    dispatch({ type: "SET_ORG_CHART_DEPT", payload: dept });
    dispatch({ type: "SET_LOADING_ORG_CHART", payload: true });
    try {
      const members = await fetchDepartmentMembers(dept.id);
      dispatch({ type: "SET_ORG_CHART_MEMBERS", payload: members });
    } catch {
      dispatch({ type: "SET_ORG_CHART_MEMBERS", payload: [] });
    } finally {
      dispatch({ type: "SET_LOADING_ORG_CHART", payload: false });
    }
  }

  async function handleSaveApprover() {
    if (ui.editingApprover) {
      try {
        await saveApproverMutation.mutateAsync({
          approver: {
            userName: ui.editingApprover.userName,
            email: ui.editingApprover.email,
            role: ui.editingApprover.role,
            level: ui.editingApprover.level,
            departmentId: ui.editingApprover.departmentId,
            canApproveAboveAmount: ui.editingApprover.canApproveAboveAmount,
          },
          isNew: false,
          id: ui.editingApprover.id,
        });
        dispatch({
          type: "SET_APPROVERS_OVERRIDE",
          payload: (prev) => (prev ?? approvers).map((a) =>
            a.id === ui.editingApprover!.id ? { ...ui.editingApprover! } : a,
          ),
        });
        dispatch({ type: "SET_EDITING_APPROVER", payload: null });
        flashSuccess("Aprovador atualizado com sucesso!");
      } catch {
        flashError("Erro ao atualizar aprovador");
      }
    } else if (ui.newApprover.userName && ui.newApprover.email) {
      try {
        const result = await saveApproverMutation.mutateAsync({ approver: ui.newApprover, isNew: true });
        const newApproverData: Approver = {
          id: result?.id || `approver-${Date.now()}`,
          userId: result?.user_id || "",
          userName: ui.newApprover.userName,
          email: ui.newApprover.email,
          role: ui.newApprover.role,
          level: ui.newApprover.level,
          isActive: true,
          departmentId: ui.newApprover.departmentId,
          canApproveAboveAmount: ui.newApprover.canApproveAboveAmount,
        };
        dispatch({ type: "SET_APPROVERS_OVERRIDE", payload: [...approvers, newApproverData] });
        flashSuccess("Aprovador criado com sucesso!");
      } catch {
        flashError("Erro ao criar aprovador");
      }
      dispatch({
        type: "SET_NEW_APPROVER",
        payload: { ...DEFAULT_NEW_APPROVER, level: approvers.length + 1 },
      });
      dispatch({ type: "SET_SHOW_APPROVER_FORM", payload: false });
    }
  }

  async function handleDeleteApprover(id: string) {
    dispatch({ type: "SET_APPROVERS_OVERRIDE", payload: approvers.filter((a) => a.id !== id) });
    try {
      await deleteApproverMutation.mutateAsync(id);
      flashSuccess("Aprovador removido com sucesso!");
    } catch {
      flashError("Erro ao remover aprovador");
    }
  }

  // ── Stable setter adapters (backward-compat with React.Dispatch signatures) ─

  const actions: UseDepartmentManagementActions = {
    setDepartments: (v) => dispatch({ type: "SET_DEPTS_OVERRIDE", payload: typeof v === "function" ? (prev) => v(prev ?? departments) : v }),
    setEditingDepartment: (v) => dispatch({ type: "SET_EDITING_DEPT", payload: v }),
    setShowDepartmentForm: (v) => dispatch({ type: "SET_SHOW_DEPT_FORM", payload: v }),
    setDepartmentToDelete: (v) => dispatch({ type: "SET_DEPT_TO_DELETE", payload: v }),
    setNewDepartment: (v) => dispatch({ type: "SET_NEW_DEPT", payload: v }),
    setIsEditingDepartments: (v) => dispatch({ type: "SET_IS_EDITING_DEPTS", payload: v }),
    setDepartmentsBackup: (v) => dispatch({ type: "SET_DEPTS_BACKUP", payload: v }),
    setShowMemberForm: (v) => dispatch({ type: "SET_SHOW_MEMBER_FORM", payload: v }),
    setEditingMember: (v) => dispatch({ type: "SET_EDITING_MEMBER", payload: v }),
    setNewMember: (v) => dispatch({ type: "SET_NEW_MEMBER", payload: v }),
    setMemberError: (v) => dispatch({ type: "SET_MEMBER_ERROR", payload: v }),
    setOrgChartDepartment: (v) => dispatch({ type: "SET_ORG_CHART_DEPT", payload: v }),
    setApprovers: (v) => dispatch({ type: "SET_APPROVERS_OVERRIDE", payload: typeof v === "function" ? (prev) => v(prev ?? approvers) : v }),
    setShowApproverForm: (v) => dispatch({ type: "SET_SHOW_APPROVER_FORM", payload: v }),
    setEditingApprover: (v) => dispatch({ type: "SET_EDITING_APPROVER", payload: v }),
    setNewApprover: (v) => dispatch({ type: "SET_NEW_APPROVER", payload: v }),
    loadDepartments,
    handleSaveDepartment,
    handleDeleteDepartment,
    handleStartEditDepartment,
    handleCancelDepartmentForm,
    handleSaveMember,
    handleEditMember,
    handleDeleteMember,
    handleOpenOrgChart,
    handleSaveApprover,
    handleDeleteApprover,
  };

  return {
    state: {
      departments,
      editingDepartment: ui.editingDepartment,
      showDepartmentForm: ui.showDepartmentForm,
      departmentToDelete: ui.departmentToDelete,
      newDepartment: ui.newDepartment,
      isEditingDepartments: ui.isEditingDepartments,
      departmentsBackup: ui.departmentsBackup,
      departmentMembers: ui.departmentMembers,
      showMemberForm: ui.showMemberForm,
      editingMember: ui.editingMember,
      savingMember: ui.savingMember,
      memberError: ui.memberError,
      memberSuccess: ui.memberSuccess,
      newMember: ui.newMember,
      orgChartDepartment: ui.orgChartDepartment,
      orgChartMembers: ui.orgChartMembers,
      loadingOrgChart: ui.loadingOrgChart,
      approvers,
      showApproverForm: ui.showApproverForm,
      editingApprover: ui.editingApprover,
      newApprover: ui.newApprover,
    },
    actions,
  };
}
