"use client";

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Chip } from "@/components/ui/chip";
import {
  Users,
  Network,
  Loader2,
  Linkedin,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  type Department,
  type DepartmentMember,
  getLevelOrder,
  getLevelLabel,
  getLevelColor,
} from '@/hooks/settings/department-types';
import { textStyles } from "@/lib/design-tokens";
import { useTranslations } from "next-intl";

export interface OrgChartDialogProps {
  orgChartDepartment: Department | null;
  orgChartMembers: DepartmentMember[];
  loadingOrgChart: boolean;
  setOrgChartDepartment: (dept: Department | null) => void;
}

export function OrgChartDialog({
  orgChartDepartment,
  orgChartMembers,
  loadingOrgChart,
  setOrgChartDepartment,
}: OrgChartDialogProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('org-chart', orgChartDepartment)

  const t = useTranslations('settings.departments');

  return (
    <Dialog
      open={!!orgChartDepartment}
      onOpenChange={() => setOrgChartDepartment(null)}
    >
      <DialogContent className="rounded-xl max-w-4xl max-h-[85vh] overflow-hidden">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-md ${orgChartDepartment?.color || "bg-lia-btn-primary-bg text-lia-btn-primary-text"} flex items-center justify-center`}
            >
              <Network className="w-5 h-5" />
            </div>
            <div>
              <DialogTitle className="text-sm">
                {t('orgChartTitle', { name: orgChartDepartment?.name || '' })}
              </DialogTitle>
              <p className={`${textStyles.description} mt-0.5`}>
                {t('orgChartEmployees', { count: orgChartMembers.length })}
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="overflow-y-auto max-h-[60vh] mt-4" role="status" aria-live="polite" aria-label={t('orgChartLoading')}>
          {loadingOrgChart ? (
            <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label={t('orgChartLoading')}>
              <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
          ) : orgChartMembers.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-12 h-12 mx-auto mb-3 text-lia-text-muted" />
              <p className="text-xs font-medium text-lia-text-secondary">
                {t('orgChartNoEmployees')}
              </p>
              <p className={`${textStyles.description} mt-1`}>
                {t('orgChartAddHint')}
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
                      <Chip variant="neutral" muted
                        className={`text-micro px-2 py-0.5 rounded-full border ${getLevelColor(level)}`}
                      >
                        {getLevelLabel(level)}
                      </Chip>
                      <div className="flex-1 h-px bg-lia-interactive-active"></div>
                      <span className="text-micro text-lia-text-tertiary">
                        {members.length}{" "}
                        {members.length === 1 ? t('person') : t('people')}
                      </span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                      {members.map((member) => (
                        <div
                          key={member.id}
                          className="flex items-center gap-3 p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-xl hover:transition-shadow"
                        >
                          <Avatar className="w-10 h-10">
                            {member.avatar_url ? (
                              <img
                                src={member.avatar_url}
                                alt={member.name}
                                className="w-full h-full object-cover rounded-full"
                              />
                            ) : (
                              <AvatarFallback className="text-xs bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary">
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
                              <p className="text-xs font-medium text-lia-text-primary truncate">
                                {member.name}
                              </p>
                              {member.linkedin_url && (
                                <a
                                  href={member.linkedin_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-brand-linkedin hover:opacity-80 flex-shrink-0"
                                >
                                  <Linkedin className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                            <p className="text-micro text-lia-text-secondary truncate">
                              {member.title || t('noTitle')}
                            </p>
                            {member.email && (
                              <p className="text-micro text-lia-text-tertiary truncate">
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
      </DialogContent>
    </Dialog>
  );
}
