"use client";

import React from"react";
import { Button } from"@/components/ui/button";
import { Card, CardContent } from"@/components/ui/card";
import { Badge } from"@/components/ui/badge";
import {
  Users,
  Network,
  Edit,
  Trash2,
  Building2,
  Maximize2,
} from"lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from"@/components/ui/alert-dialog";
import { type Department } from './companyTeamHub.types';

export interface DepartmentGridProps {
  departments: Department[];
  showDepartmentForm: boolean;
  departmentToDelete: Department | null;
  isEditingDepartments: boolean;
  setDepartmentToDelete: (dept: Department | null) => void;
  handleStartEditDepartment: (dept: Department) => void;
  handleDeleteDepartment: (id: string) => Promise<void>;
  handleOpenOrgChart: (dept: Department) => Promise<void>;
}

export function DepartmentGrid({
  departments,
  showDepartmentForm,
  departmentToDelete,
  isEditingDepartments,
  setDepartmentToDelete,
  handleStartEditDepartment,
  handleDeleteDepartment,
  handleOpenOrgChart,
}: DepartmentGridProps) {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {departments.length === 0 && !showDepartmentForm ? (
          <div className="col-span-2 text-center py-8 text-lia-text-secondary">
            <Network className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-xs font-medium text-lia-text-primary">
              Nenhum departamento cadastrado
            </p>
            <p className="text-xs mt-1 text-lia-text-secondary">
              Clique em"Novo Departamento" ou importe uma planilha para começar
            </p>
          </div>
        ) : (
          departments.map((dept) => (
            <Card
              key={dept.id}
              className="border border-lia-border-subtle/50 dark:border-lia-border-subtle/50 bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-xl hover:transition-shadow"
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
                      <h4 className="text-xs font-semibold text-lia-text-primary">
                        {dept.name}
                      </h4>
                      <p className="text-micro text-lia-text-secondary">
                        {dept.description}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                      onClick={() => handleOpenOrgChart(dept)}
                      title="Ver organograma"
                    >
                      <Maximize2 className="w-3.5 h-3.5 text-lia-text-secondary" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 rounded-xl hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse"
                      onClick={() => handleStartEditDepartment(dept)}
                      disabled={!isEditingDepartments}
                    >
                      <Edit className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 w-7 p-0 rounded-md text-status-error hover:text-status-error hover:bg-status-error/10"
                      onClick={() => setDepartmentToDelete(dept)}
                      disabled={!isEditingDepartments}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-lia-border-subtle dark:border-lia-border-strong flex items-center justify-between">
                  <div className="flex items-center gap-2 text-micro text-lia-text-secondary">
                    <Users className="w-3 h-3" />
                    <span>{dept.headcount} colaboradores</span>
                  </div>
                  {dept.manager && (
                    <Badge
                      variant="outline"
                      className="text-micro rounded-xl border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary"
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
            <AlertDialogTitle className="text-sm font-semibold text-lia-text-primary">
              Excluir Departamento
            </AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir o departamento"
              {departmentToDelete?.name}"? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-md text-xs">
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              className="rounded-md text-xs bg-status-error hover:bg-status-error"
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
    </>
  );
}
