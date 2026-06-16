"use client"

import React, { useState } from "react"
import { useTranslations } from "next-intl"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Calendar, Mail, MessageSquare, Star, Briefcase, User, Phone, Linkedin, X } from"lucide-react"
import { LIAIcon } from"@/components/ui/lia-icon"
import { LIAFeedbackWidget } from"@/components/calibration"
import { CandidateChatPopover } from "@/components/shared/CandidateChatPopover"
import { textStyles, badgeStyles, formatScore, formatScorePercent } from"@/lib/design-tokens"
import type { Candidate } from"@/components/pages/candidates/types"

export function CandidatePreviewPanel({ candidate, onClose }: { candidate: Candidate; onClose: () => void }) {
    const t = useTranslations("candidates.preview")

    const [activeTab, setActiveTab] = useState("overview")

    const tabs = [
      { id: "overview", label: t("tabs.overview"), icon: User },
      { id: "experience", label: t("tabs.experience"), icon: Briefcase },
      { id: "skills", label: t("tabs.skills"), icon: Star },
      { id: "contact", label: t("tabs.contact"), icon: MessageSquare }
    ]

    const renderTabContent = () => {
      switch (activeTab) {
        case "overview":
          return (
            <div className="space-y-6">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-primary mb-2">{t("basicInfo")}</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <span className={textStyles.bodySmall}>{t("position")}</span>
                    <span className={`${textStyles.label} text-lia-text-primary`}>{candidate.position}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <span className={textStyles.bodySmall}>{t("locationLabel")}</span>
                    <span className={`${textStyles.label} text-lia-text-primary`}>{candidate.location}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <span className={textStyles.bodySmall}>{t("statusLabel")}</span>
                    <Chip variant="neutral" muted className={[
                      candidate.status === "active" ? badgeStyles.success :
                      candidate.status === "prospect" ? badgeStyles.info :
                      candidate.status === "interview" ? badgeStyles.warning :
                      badgeStyles.default,
                      "px-2 py-0.5"
                    ].join(" ")}>
                      {candidate.status === "active" ? t("statusActive") :
                       candidate.status === "prospect" ? t("statusProspect") :
                       candidate.status === "interview" ? t("statusInterview") : t("statusHired")}
                    </Chip>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-lia-text-primary mb-2">{t("scoreLia")}</h4>
                <div className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary p-3 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className={textStyles.label}>{t("compatibility")}</span>
                    <span className="text-base font-bold text-lia-text-primary">{formatScorePercent(candidate.score)}</span>
                  </div>
                  <div className="w-full bg-lia-interactive-active rounded-full h-1.5">
                    <div
                      className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary h-1.5 rounded-full"
                      style={{width: String(formatScore(candidate.score)) + "%"}}
                    ></div>
                  </div>
                  <div className={textStyles.description + " mt-1"}>
                    {t("scoreDescription")}
                  </div>
                  <div className="mt-3 pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <LIAFeedbackWidget
                      candidateId={candidate.id}
                      liaScore={candidate.score}
                      liaRecommendation={candidate.liaAnalysis?.recommendation}
                      compact={false}
                      showLabel={true}
                    />
                  </div>
                </div>
              </div>
            </div>
          )

        case "experience":
          return (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-primary mb-2">{t("professionalExperience")}</h4>
                {candidate.workHistory && candidate.workHistory.length > 0 ? (
                  <div className="space-y-3">
                    {candidate.workHistory.slice(0, 4).map((exp, i) => (
                      <div key={i} className={[
                        "border-l-4 pl-3 py-2 rounded-r-lg",
                        i === 0
                          ? "border-wedo-green bg-wedo-green/10 dark:bg-wedo-green/20"
                          : "border-lia-border-default bg-lia-bg-secondary dark:bg-lia-bg-secondary"
                      ].join(" ")}>
                        <div className={textStyles.label + " text-lia-text-primary"}>
                          {exp.title || exp.role || exp.position || ""}
                        </div>
                        <div className={[textStyles.bodySmall, i === 0 ? "text-lia-text-secondary dark:text-wedo-green" : ""].join(" ")}>
                          {[
                            exp.company,
                            exp.period || (exp.startDate
                              ? exp.startDate + (exp.endDate ? " - " + exp.endDate : " - " + t("current"))
                              : null)
                          ].filter(Boolean).join(" • ")}
                        </div>
                        {exp.description ? (
                          <div className={textStyles.bodySmall + " mt-1"}>
                            {exp.description}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>
          )

        case "skills": {
          const technicalSkills = (candidate.technical_skills && candidate.technical_skills.length > 0)
            ? candidate.technical_skills
            : (candidate.skills && candidate.skills.length > 0)
            ? candidate.skills
            : null
          const softSkillsList = (candidate.soft_skills && candidate.soft_skills.length > 0)
            ? candidate.soft_skills
            : null

          return (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-primary mb-2">{t("technicalSkills")}</h4>
                {technicalSkills ? (
                  <div className="flex flex-wrap gap-1">
                    {technicalSkills.map((skill) => (
                      <Chip density="relaxed" variant="neutral" muted key={skill} className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-0">
                        {skill}
                      </Chip>
                    ))}
                  </div>
                ) : null}
              </div>
              {softSkillsList ? (
                <div>
                  <h4 className="text-xs font-medium text-lia-text-primary mb-2">{t("softSkills")}</h4>
                  <div className="flex flex-wrap gap-2">
                    {softSkillsList.map((skill, index) => (
                      <Chip density="relaxed" variant="neutral" muted key={index} className="border-0">
                        {skill}
                      </Chip>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          )
        }

        case "contact":
          return (
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-lia-text-primary mb-3">{t("contactInfo")}</h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <Mail className="w-4 h-4 text-lia-text-primary" />
                    <div>
                      <div className="text-sm font-medium text-lia-text-primary">{candidate.email}</div>
                      <div className="text-xs text-lia-text-primary">{t("primaryEmail")}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <Phone className="w-4 h-4 text-lia-text-primary" />
                    <div>
                      <div className="text-sm font-medium text-lia-text-primary">{candidate.phone}</div>
                      <div className="text-xs text-lia-text-primary">{t("phoneWhatsapp")}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <Linkedin className="w-4 h-4 text-lia-text-secondary" />
                    <div>
                      <div className="text-sm font-medium text-lia-text-primary">{t("viewLinkedinProfile")}</div>
                      <div className="text-xs text-lia-text-primary">{t("professionalProfile")}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )

        default:
          return null
      }
    }

    return (
      <div className="w-96 bg-lia-bg-primary dark:bg-lia-bg-secondary border-l border-lia-border-subtle dark:border-lia-border-subtle flex flex-col h-full">
        <div className="p-4 dark:border-lia-border-subtle">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage
                  src={candidate.avatar || ("https://ui-avatars.com/api/?name=" + encodeURIComponent(candidate.name) + "&background=60BED1&color=fff&size=150")}
                  alt={candidate.name}
                />
                <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary font-semibold">
                  {candidate.name.split(" ").map((n: string) => n[0]).join("").toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <div className="flex items-center gap-1.5">
                  <CandidateChatPopover candidateId={candidate.id} candidateName={candidate.name}>
                    <h3 className="font-semibold text-lia-text-primary">{candidate.name}</h3>
                  </CandidateChatPopover>
                </div>
                <p className="text-sm text-lia-text-primary">{candidate.position}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="text-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <div className="font-semibold text-lia-text-primary">{formatScorePercent(candidate.score)}</div>
              <div className="text-lia-text-primary">{t("scoreLia")}</div>
            </div>
            <div className="text-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <Chip variant="neutral" muted className={[
                "text-xs",
                candidate.status === "active" ? "bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success" :
                candidate.status === "prospect" ? "bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary" :
                candidate.status === "interview" ? "bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning" :
                "bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary"
              ].join(" ")}>
                {candidate.status === "active" ? t("statusActive") :
                 candidate.status === "prospect" ? t("statusProspect") :
                 candidate.status === "interview" ? t("statusInterview") : t("statusHired")}
              </Chip>
            </div>
          </div>
        </div>

        <div className="dark:border-lia-border-subtle">
          <nav className="flex space-x-0" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={[
                  "flex-1 py-2 px-3 text-xs font-medium text-center rounded-lg",
                  activeTab === tab.id
                    ? "border-lia-btn-primary-bg text-lia-text-primary dark:border-lia-border-medium"
                    : "border-transparent text-lia-text-primary hover:text-lia-text-primary hover:border-lia-border-default"
                ].join(" ")}
              >
                <tab.icon className="w-3 h-3 mx-auto mb-1" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {renderTabContent()}
        </div>

        <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle space-y-2">
          <Button
            className="w-full gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
            onClick={() => {}}
          >
            <Calendar className="w-4 h-4" />
            {t("scheduleInterview")}
          </Button>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => {}}
            >
              <Mail className="w-4 h-4" />
              Email
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => {}}
            >
              <LIAIcon size="sm" />
              LIA
            </Button>
          </div>
        </div>
      </div>
    )
}
