"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Building, Globe, MessageSquare, Target, Network,
  Upload, FileText, Heart, Edit, Trash2, Plus
} from "lucide-react"
import {
  BasicDataSection,
  AddressSection,
  SocialMediaSection,
  SegmentSection,
  BranchesSection
} from "./institutional-tab-sections"

export interface SettingsCompanyTabProps {
  onSettingsChange: (changed: boolean) => void
}

type InstitutionalSubTab = 'basic' | 'address' | 'social' | 'segment' | 'branches'

export function InstitutionalTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const [activeSubTab, setActiveSubTab] = useState<InstitutionalSubTab>('basic')
  const t = useTranslations("settings.institutionalSubTabs")

  const subTabs = [
    { id: 'basic' as const, name: t("basicData"), icon: Building },
    { id: 'address' as const, name: t("address"), icon: Globe },
    { id: 'social' as const, name: t("socialMedia"), icon: MessageSquare },
    { id: 'segment' as const, name: t("segment"), icon: Target },
    { id: 'branches' as const, name: t("branches"), icon: Network }
  ]

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-1 overflow-x-auto">
            {subTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 rounded-md text-sm font-medium whitespace-nowrap transition-colors motion-reduce:transition-none ${
                  activeSubTab === tab.id
 ? 'bg-lia-bg-primary shadow-sm dark:bg-lia-bg-primary text-lia-text-primary'
                    : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover text-lia-text-primary'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.name}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {activeSubTab === 'basic' && <BasicDataSection onSettingsChange={onSettingsChange} />}
      {activeSubTab === 'address' && <AddressSection onSettingsChange={onSettingsChange} />}
      {activeSubTab === 'social' && <SocialMediaSection onSettingsChange={onSettingsChange} />}
      {activeSubTab === 'segment' && <SegmentSection onSettingsChange={onSettingsChange} />}
      {activeSubTab === 'branches' && <BranchesSection />}
    </div>
  )
}

export function CultureTab({ onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const t = useTranslations("settings.companyTabs.cultureTab")
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Heart className="w-4 h-4" />
            {t("corporateIdentity")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("mission")}
            </label>
            <textarea
              key={t("missionDefault")}
              rows={3}
              defaultValue={t("missionDefault")}
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("vision")}
            </label>
            <textarea
              key={t("visionDefault")}
              rows={3}
              defaultValue={t("visionDefault")}
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-lia-text-primary mb-3 block">
              {t("purpose")}
            </label>
            <textarea
              key={t("purposeDefault")}
              rows={3}
              defaultValue={t("purposeDefault")}
              onChange={() => onSettingsChange(true)}
              className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-xl bg-lia-bg-primary dark:bg-lia-bg-secondary text-sm"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("companyValues")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {[
              { key: 'value1', value: t("value1Name"), description: t("value1Desc") },
              { key: 'value2', value: t("value2Name"), description: t("value2Desc") },
              { key: 'value3', value: t("value3Name"), description: t("value3Desc") },
              { key: 'value4', value: t("value4Name"), description: t("value4Desc") }
            ].map((item) => (
              <div key={item.key} className="p-4 border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-lia-text-primary">
                    {item.value}
                  </h4>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Edit className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                <p className="text-xs text-lia-text-primary">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
          <Button variant="outline" className="gap-2" size="sm">
            <Plus className="w-4 h-4" />
            {t("addValue")}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

export function StructureTab({ onSettingsChange: _onSettingsChange }: { onSettingsChange: (changed: boolean) => void }) {
  const t = useTranslations("settings.companyTabs.structureTab")
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-semibold">
            <Network className="w-4 h-4" />
            {t("orgChartTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-xl p-8 text-center bg-lia-bg-secondary dark:bg-lia-bg-secondary">
            <Upload className="w-12 h-12 mx-auto mb-4 text-lia-text-primary" />
            <h4 className="text-sm font-medium text-lia-text-primary mb-2">
              {t("orgChartUploadText")}
            </h4>
            <p className="text-sm text-lia-text-primary mb-4">
              {t("orgChartFormats")}
            </p>
            <Button variant="outline">
              {t("chooseFile")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("jobsStructureTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-xl p-6 text-center mb-4 bg-lia-bg-secondary dark:bg-lia-bg-secondary">
            <FileText className="w-8 h-8 mx-auto mb-2 text-lia-text-primary" />
            <p className="text-sm text-lia-text-primary mb-2">
              {t("jobsUploadText")}
            </p>
            <p className="text-xs text-lia-text-primary mb-3">{t("jobsFormats")}</p>
            <Button variant="outline" size="sm">
              {t("uploadJobs")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
