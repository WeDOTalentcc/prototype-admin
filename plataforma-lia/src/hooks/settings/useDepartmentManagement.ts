import { useState, useEffect, useRef } from "react";
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
  setDepartments: React.Dispatch<React.SetStateAction<Department[]>>;
  setEditingDepartment: (dept: Department | null) => void;
  setShowDepartmentForm: (show: boolean) => void;
  setDepartmentToDelete: (dept: Department | null) => void;
  setNewDepartment: React.Dispatch<React.SetStateAction<NewDepartmentForm>>;
  setIsEditingDepartments: (editing: boolean) => void;
  setDepartmentsBackup: (backup: Department[]) => void;
  setShowMemberForm: (show: boolean) => void;
  setEditingMember: (member: DepartmentMember | null) => void;
  setNewMember: React.Dispatch<React.SetStateAction<NewMemberForm>>;
  setMemberError: (error: string | null) => void;
  setOrgChartDepartment: (dept: Department | null) => void;
  setApprovers: React.Dispatch<React.SetStateAction<Approver[]>>;
  setShowApproverForm: (show: boolean) => void;
  setEditingApprover: (approver: Approver | null) => void;
  setNewApprover: React.Dispatch<React.SetStateAction<NewApproverForm>>;
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

export function useDepartmentManagement({
  initialDepartments,
  initialApprovers,
  setError,
  setSuccessMessage,
}: UseDepartmentManagementOptions): UseDepartmentManagementResult {
  const { companyId } = useCompanyId();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null);
  const [showDepartmentForm, setShowDepartmentForm] = useState(false);
  const [departmentToDelete, setDepartmentToDelete] = useState<Department | null>(null);
  const [newDepartment, setNewDepartment] = useState<NewDepartmentForm>(DEFAULT_NEW_DEPARTMENT);
  const [isEditingDepartments, setIsEditingDepartments] = useState(false);
  const [departmentsBackup, setDepartmentsBackup] = useState<Department[]>([]);
  const [departmentMembers, setDepartmentMembers] = useState<DepartmentMember[]>([]);
  const [showMemberForm, setShowMemberForm] = useState(false);
  const [editingMember, setEditingMember] = useState<DepartmentMember | null>(null);
  const [savingMember, setSavingMember] = useState(false);
  const [memberError, setMemberError] = useState<string | null>(null);
  const [memberSuccess, setMemberSuccess] = useState<string | null>(null);
  const [newMember, setNewMember] = useState<NewMemberForm>(DEFAULT_NEW_MEMBER);
  const [orgChartDepartment, setOrgChartDepartment] = useState<Department | null>(null);
  const [orgChartMembers, setOrgChartMembers] = useState<DepartmentMember[]>([]);
  const [loadingOrgChart, setLoadingOrgChart] = useState(false);
  const [approvers, setApprovers] = useState<Approver[]>([]);
  const [showApproverForm, setShowApproverForm] = useState(false);
  const [editingApprover, setEditingApprover] = useState<Approver | null>(null);
  const [newApprover, setNewApprover] = useState<NewApproverForm>({
    userName: "",
    email: "",
    role: "",
    level: 1,
    departmentId: null,
    canApproveAboveAmount: null,
  });

  const isMountedRef = useRef(true);
  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);

  useEffect(() => {
    if (initialDepartments.length > 0) {
      setDepartments(initialDepartments);
    }
  }, [initialDepartments]);

  useEffect(() => {
    if (initialApprovers.length > 0) {
      setApprovers(initialApprovers);
    }
  }, [initialApprovers]);

  const loadDepartments = async () => {
    try {
      const response = await fetch("/api/backend-proxy/company/departments");
      if (response.ok) {
        const departmentsResult = await response.json();
        if (Array.isArray(departmentsResult) && departmentsResult.length > 0) {
          setDepartments(
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
        } else {
          setDepartments([]);
        }
      }
    } catch (err) {
      console.error("[Departments] loadDepartments failed:", err)
      toast.error("Falha ao carregar departamentos. Tente novamente.")
    }
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
      setDepartmentMembers([]);
    }
  };

  const saveDepartmentToAPI = async (dept: Department, isNew: boolean) => {
    try {
      const method = isNew ? "POST" : "PUT";
      const url = isNew
        ? `/api/backend-proxy/company/departments?company_id=${encodeURIComponent(companyId || "")}`
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
      throw err;
    }
  };

  const deleteDepartmentFromAPI = async (id: string) => {
    try {
      const response = await fetch(
        `/api/backend-proxy/company/departments/${id}`,
        { method: "DELETE" },
      );
      if (!response.ok) {
        throw new Error("Falha ao remover departamento");
      }
      notifyChatOfSettingsUpdate({
        actionId: "delete_department",
        section: "departments",
        field: id,
      });
    } catch (err) {
      console.error("[Departments] deleteDepartmentFromAPI failed:", err)
      throw err
    }
  };

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
        { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000); }
      } catch (err) {
        setError("Erro ao atualizar departamento");
        { const _t = setTimeout(() => { if (isMountedRef.current) setError(null); }, 3000); }
      }
      setEditingDepartment(null);
      setNewDepartment({ ...DEFAULT_NEW_DEPARTMENT });
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
        { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000); }
      } catch (err) {
        setDepartments((prev) => [...prev, dept]);
      }
      setNewDepartment({ ...DEFAULT_NEW_DEPARTMENT });
      setShowDepartmentForm(false);
    }
  };

  const handleDeleteDepartment = async (id: string) => {
    setDepartments((prev) => prev.filter((d) => d.id !== id));
    try {
      await deleteDepartmentFromAPI(id);
      setSuccessMessage("Departamento removido com sucesso!");
      { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000); }
    } catch (err) {
      setError("Erro ao remover departamento");
      { const _t = setTimeout(() => { if (isMountedRef.current) setError(null); }, 3000); }
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
    setNewDepartment({ ...DEFAULT_NEW_DEPARTMENT });
    setDepartmentMembers([]);
    setShowMemberForm(false);
    setEditingMember(null);
    setNewMember({ ...DEFAULT_NEW_MEMBER });
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
        setNewMember({ ...DEFAULT_NEW_MEMBER });
        setShowMemberForm(false);
        setEditingMember(null);
        setMemberSuccess(
          editingMember
            ? "Colaborador atualizado com sucesso!"
            : "Colaborador adicionado com sucesso!",
        );
        { const _t = setTimeout(() => { if (isMountedRef.current) setMemberSuccess(null); }, 3000); }
      } else {
        const errorData = await res.json().catch(() => ({}));
        setMemberError(errorData.detail || "Erro ao salvar colaborador");
      }
    } catch (err) {
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
      notifyChatOfSettingsUpdate({
        actionId: "delete_department_member",
        section: "departments",
        field: memberId,
      });
      if (editingDepartment) {
        await loadDepartmentMembers(editingDepartment.id);
      }
    } catch (err) {
      console.error("[Departments] handleDeleteMember failed:", err)
      toast.error("Falha ao remover membro. Tente novamente.")
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
      setOrgChartMembers([]);
    } finally {
      setLoadingOrgChart(false);
    }
  };

  const saveApproverToAPI = async (
    approver: {
      userName: string;
      email: string;
      role: string;
      level: number;
      departmentId: string | null;
      canApproveAboveAmount: number | null;
    },
    isNew: boolean,
    id?: string,
  ) => {
    try {
      const method = isNew ? "POST" : "PUT";
      const url = isNew
        ? `/api/backend-proxy/company/approvers?company_id=${encodeURIComponent(companyId || "")}`
        : `/api/backend-proxy/company/approvers/${id}`;

      const response = await fetch(url, {
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

      if (!response.ok) {
        throw new Error("Falha ao salvar aprovador");
      }

      const result = await response.json();
      return result;
    } catch (err) {
      throw err;
    }
  };

  const deleteApproverFromAPI = async (id: string) => {
    try {
      const response = await fetch(
        `/api/backend-proxy/company/approvers/${id}`,
        { method: "DELETE" },
      );
      if (!response.ok) {
        throw new Error("Falha ao remover aprovador");
      }
      notifyChatOfSettingsUpdate({
        actionId: "delete_approver",
        section: "departments",
        field: id,
      });
    } catch (err) {
      console.error("[Departments] deleteApproverFromAPI failed:", err)
      throw err
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
            departmentId: editingApprover.departmentId,
            canApproveAboveAmount: editingApprover.canApproveAboveAmount,
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
        { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000); }
      } catch (err) {
        setError("Erro ao atualizar aprovador");
        { const _t = setTimeout(() => { if (isMountedRef.current) setError(null); }, 3000); }
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
          departmentId: newApprover.departmentId,
          canApproveAboveAmount: newApprover.canApproveAboveAmount,
        };
        setApprovers((prev) => [...prev, newApproverData]);
        setSuccessMessage("Aprovador criado com sucesso!");
        { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000); }
      } catch (err) {
        setError("Erro ao criar aprovador");
        { const _t = setTimeout(() => { if (isMountedRef.current) setError(null); }, 3000); }
      }
      setNewApprover({
        userName: "",
        email: "",
        role: "",
        level: approvers.length + 1,
        departmentId: null,
        canApproveAboveAmount: null,
      });
      setShowApproverForm(false);
    }
  };

  const handleDeleteApprover = async (id: string) => {
    setApprovers((prev) => prev.filter((a) => a.id !== id));
    try {
      await deleteApproverFromAPI(id);
      setSuccessMessage("Aprovador removido com sucesso!");
      { const _t = setTimeout(() => { if (isMountedRef.current) setSuccessMessage(null); }, 3000); }
    } catch (err) {
      setError("Erro ao remover aprovador");
      { const _t = setTimeout(() => { if (isMountedRef.current) setError(null); }, 3000); }
    }
  };

  return {
    state: {
      departments,
      editingDepartment,
      showDepartmentForm,
      departmentToDelete,
      newDepartment,
      isEditingDepartments,
      departmentsBackup,
      departmentMembers,
      showMemberForm,
      editingMember,
      savingMember,
      memberError,
      memberSuccess,
      newMember,
      orgChartDepartment,
      orgChartMembers,
      loadingOrgChart,
      approvers,
      showApproverForm,
      editingApprover,
      newApprover,
    },
    actions: {
      setDepartments,
      setEditingDepartment,
      setShowDepartmentForm,
      setDepartmentToDelete,
      setNewDepartment,
      setIsEditingDepartments,
      setDepartmentsBackup,
      setShowMemberForm,
      setEditingMember,
      setNewMember,
      setMemberError,
      setOrgChartDepartment,
      setApprovers,
      setShowApproverForm,
      setEditingApprover,
      setNewApprover,
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
    },
  };
}
