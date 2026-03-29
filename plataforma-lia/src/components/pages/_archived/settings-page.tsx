"use client"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { RotateCcw, Save } from "lucide-react"
import { useSettingsNavigation } from "@/hooks/useSettingsNavigation"
import { useSettingsForm } from "@/hooks/useSettingsForm"
import { SettingsGeneralTab } from "@/components/settings/settings-general-tab"
import { SettingsNotificationsTab } from "@/components/settings/settings-notifications-tab"
import { SettingsSecurityTab } from "@/components/settings/settings-security-tab"
import { SettingsIntegrationsTab } from "@/components/settings/settings-integrations-tab"
import { SettingsBillingTab } from "@/components/settings/settings-billing-tab"
import { SettingsAPIKeysTab } from "@/components/settings/settings-api-keys-tab"
import { SettingsJourneyTab } from "@/components/settings/settings-journey-tab"
import { InstitutionalTab, CultureTab, StructureTab } from "@/components/settings/settings-company-tabs"
import {
  CommunicationTab,
  RecruitmentJourneyTab,
  AssessmentTab,
  AutomationsTab,
  NPSTab
} from "@/components/settings/settings-recruitment-tabs"

export function SettingsPage() {
  const { state: navState, actions: navActions } = useSettingsNavigation()
  const { state: formState, actions: formActions } = useSettingsForm()

  const { activeTab, sidebarWidth, isResizing, tabs, categories } = navState
  const { setActiveTab, startResize } = navActions
  const { hasChanges } = formState
  const { setHasChanges, handleSave, handleReset } = formActions

  return (
    <div className="space-y-4 settings-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-sm font-semibold text-gray-950 dark:text-gray-50 font-inter">Configurações</h1>
          <p className="text-xs text-gray-800 dark:text-gray-400">
            Configure sua plataforma, empresa e processos de recrutamento
          </p>
        </div>

        {hasChanges && (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleReset}>
              <RotateCcw className="w-4 h-4 mr-2" />
              Descartar
            </Button>
            <Button size="sm" onClick={handleSave}>
              <Save className="w-4 h-4 mr-2" />
              Salvar Alterações
            </Button>
          </div>
        )}
      </div>

      <div className="flex gap-4">
        <div
          className="relative flex-shrink-0 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700"
          style={{width: `${sidebarWidth}px`, minWidth: '200px', maxWidth: '400px'}}
        >
          <nav className="space-y-4 p-4 h-full overflow-y-auto">
            {categories.map((category) => (
              <div key={category.id}>
                <h3 className="text-xs font-semibold text-gray-800 dark:text-gray-200 uppercase tracking-wider mb-4 font-inter 2xl:text-xs">
                  {category.name}
                </h3>
                <div className="space-y-1">
                  {tabs.filter(tab => tab.category === category.id).map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-3 py-3 rounded-md text-left transition-colors font-open-sans settings-menu-item ${
                        activeTab === tab.id
 ? 'bg-gray-50 dark:bg-gray-800 border border-gray-900 dark:border-gray-200 text-gray-900 dark:text-gray-300'
                          : 'hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-800 dark:text-gray-200'
                      }`}
                      style={{fontSize: '0.6875rem', lineHeight: '1.125rem', fontWeight: '500'}}
                    >
                      <tab.icon className="w-4 h-4" />
                      <div>
                        <div className="text-sm font-medium 2xl:text-xs">{tab.name}</div>
                        <div className="text-xs text-gray-800 dark:text-gray-400 2xl:text-xs">{tab.description}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </nav>

          <div
            className={cn(
              "absolute top-0 right-0 w-1 h-full cursor-col-resize group z-10",
              "hover:w-1.5 transition-all duration-200",
              isResizing ? "bg-gray-400 w-1.5" : "bg-transparent hover:bg-gray-500"
            )}
            onMouseDown={startResize}
            title="Arrastar para redimensionar menu de configurações"
          >
            <div className="absolute inset-y-0 right-0 w-px bg-gray-200 dark:bg-gray-700 group-hover:bg-wedo-cyan/10 transition-colors duration-200" />
            <div className="absolute top-0 -right-2 w-4 h-full" />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="space-y-6">
            {activeTab === "preferences" && <SettingsGeneralTab onSettingsChange={setHasChanges} />}
            {activeTab === "lia" && <SettingsGeneralTab onSettingsChange={setHasChanges} />}
            {activeTab === "notifications" && <SettingsNotificationsTab onSettingsChange={setHasChanges} />}
            {activeTab === "institutional" && <InstitutionalTab onSettingsChange={setHasChanges} />}
            {activeTab === "culture" && <CultureTab onSettingsChange={setHasChanges} />}
            {activeTab === "structure" && <StructureTab onSettingsChange={setHasChanges} />}
            {activeTab === "communication" && <CommunicationTab onSettingsChange={setHasChanges} />}
            {activeTab === "journey-mapping" && <SettingsJourneyTab onSettingsChange={setHasChanges} />}
            {activeTab === "recruitment-journey" && <RecruitmentJourneyTab onSettingsChange={setHasChanges} />}
            {activeTab === "assessment" && <AssessmentTab onSettingsChange={setHasChanges} />}
            {activeTab === "automations" && <AutomationsTab onSettingsChange={setHasChanges} />}
            {activeTab === "nps" && <NPSTab onSettingsChange={setHasChanges} />}
            {activeTab === "integrations" && <SettingsIntegrationsTab onSettingsChange={setHasChanges} />}
            {activeTab === "security" && <SettingsSecurityTab onSettingsChange={setHasChanges} />}
            {activeTab === "admin-wedotalent" && <SettingsBillingTab onSettingsChange={setHasChanges} />}
          </div>
        </div>
      </div>

      {isResizing && (
        <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-black dark:bg-white text-white dark:text-black text-sm px-3 py-2 rounded-md z-50 pointer-events-none">
          {sidebarWidth}px
        </div>
      )}
    </div>
  )
}
