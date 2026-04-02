"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Plus,
  Edit,
  Trash2,
  Save,
  CheckCircle,
  AlertCircle,
  Crown,
} from "lucide-react";
import {
  type Approver,
  type NewApproverForm,
} from "./companyTeamHub.types";

export interface ApproverSectionProps {
  approvers: Approver[];
  showApproverForm: boolean;
  editingApprover: Approver | null;
  newApprover: NewApproverForm;
  successMessage: string | null;
  error: string | null;
  setShowApproverForm: (show: boolean) => void;
  setEditingApprover: (approver: Approver | null) => void;
  setNewApprover: React.Dispatch<React.SetStateAction<NewApproverForm>>;
  handleSaveApprover: () => Promise<void>;
  handleDeleteApprover: (id: string) => Promise<void>;
}

export const ApproverSection = React.memo(function ApproverSection({
  approvers,
  showApproverForm,
  editingApprover,
  newApprover,
  successMessage,
  error,
  setShowApproverForm,
  setEditingApprover,
  setNewApprover,
  handleSaveApprover,
  handleDeleteApprover,
}: ApproverSectionProps) {
  return (
    <div className="space-y-3">
      {successMessage && (
        <div className="bg-status-success/10 border border-status-success/30 rounded-md p-2 flex items-center gap-2 text-status-success text-xs">
          <CheckCircle className="w-3.5 h-3.5" />
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 rounded-md p-2 flex items-center gap-2 text-status-error text-xs">
          <AlertCircle className="w-3.5 h-3.5" />
          {error}
        </div>
      )}

      <Card className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base-ui font-semibold flex items-center gap-2">
                <Crown className="w-3.5 h-3.5 text-lia-text-secondary" />
                Fluxo de Aprovação de Vagas
              </CardTitle>
              <p className="text-xs text-lia-text-secondary mt-1" aria-live="polite" aria-atomic="true">
                Configure os níveis de aprovação para abertura de vagas
              </p>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="gap-1.5 py-1.5 px-2 text-xs rounded-full border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
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
            <Card className="border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md mb-3">
              <CardContent className="p-3 space-y-2">
                <h4 className="text-xs font-semibold">
                  {editingApprover ? "Editar Aprovador" : "Novo Aprovador"}
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      Nome
                    </label>
                    <input
                      type="text"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                      placeholder="Nome do aprovador"
                      value={editingApprover ? editingApprover.userName : newApprover.userName}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, userName: e.target.value })
                          : setNewApprover((prev) => ({ ...prev, userName: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                      placeholder="email@empresa.com"
                      value={editingApprover ? editingApprover.email : newApprover.email}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, email: e.target.value })
                          : setNewApprover((prev) => ({ ...prev, email: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      Cargo
                    </label>
                    <input
                      type="text"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                      placeholder="Ex: Gerente de RH"
                      value={editingApprover ? editingApprover.role : newApprover.role}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, role: e.target.value })
                          : setNewApprover((prev) => ({ ...prev, role: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-micro font-medium text-lia-text-secondary mb-1">
                      Nível de Aprovação
                    </label>
                    <input
                      type="number"
                      min="1"
                      className="w-full px-2 py-1.5 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary text-xs"
                      value={editingApprover ? editingApprover.level : newApprover.level}
                      onChange={(e) =>
                        editingApprover
                          ? setEditingApprover({ ...editingApprover, level: parseInt(e.target.value) || 1 })
                          : setNewApprover((prev) => ({ ...prev, level: parseInt(e.target.value) || 1 }))
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
                    className="py-1.5 px-2 text-xs rounded-full"
                  >
                    Cancelar
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSaveApprover}
                    className="py-1.5 px-2 text-xs rounded-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
                  >
                    <Save className="w-3.5 h-3.5 mr-1" />
                    Salvar
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {approvers.length === 0 && !showApproverForm ? (
            <div className="text-center py-6 text-lia-text-secondary">
              <Crown className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-xs">
                Nenhum aprovador configurado
              </p>
              <p className="text-micro mt-1">
                Clique em "Adicionar Nível" para criar um fluxo de aprovação
              </p>
            </div>
          ) : (
            <div className="relative">
              <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-lia-interactive-active dark:bg-lia-bg-elevated" />
              {approvers
                .sort((a, b) => a.level - b.level)
                .map((approver) => (
                  <div
                    key={approver.id}
                    className="relative flex items-center gap-3 pb-4 last:pb-0"
                  >
                    <div
                      className=""
                    >
                      {approver.level}
                    </div>
                    <Card className="flex-1 border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md">
                      <CardContent className="p-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary text-micro">
                              {approver.userName
                                .split(" ")
                                .map((n) => n[0])
                                .join("")}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="text-xs font-semibold text-lia-text-primary">
                              {approver.userName}
                            </p>
                            <p className="text-micro text-lia-text-secondary">
                              {approver.role} • {approver.email}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Badge
                            variant={approver.isActive ? "default" : "outline"}
                            className=""
                          >
                            {approver.isActive ? "Ativo" : "Inativo"}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                            onClick={() => setEditingApprover(approver)}
                          >
                            <Edit className="w-3.5 h-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0 rounded-md text-status-error hover:text-status-error hover:bg-status-error/10"
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

          <div className="bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md p-2 border border-lia-border-subtle dark:border-lia-border-subtle">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-lia-text-secondary" />
              <div>
                <p className="text-xs font-semibold text-lia-text-primary">
                  Fluxo de Aprovação
                </p>
                <p className="text-micro mt-0.5 text-lia-text-secondary" aria-live="polite" aria-atomic="true">
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
});
