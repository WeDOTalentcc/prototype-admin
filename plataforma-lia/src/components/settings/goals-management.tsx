"use client"

import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Badge } from"@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  Plus, Target, Users, Settings,
  CheckCircle, AlertCircle, Loader2,
  ChevronDown, ChevronUp
} from"lucide-react"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from"@/components/ui/select"
import { useTranslations } from "next-intl"
import { textStyles } from"@/lib/design-tokens"
import { EditableCell, GoalsStatsCards, getCategoryIcon, getCategoryColor } from"./goals"
import { ApplyAllModal, DeleteConfirmModal } from"./goals"
import { GoalsTemplatesModal } from"./goals-templates-modal"
import { GoalsCustomGoalModal } from"./goals-custom-goal-modal"
import { GoalsEditGoalModal, GoalsEditTemplateModal } from"./goals-edit-modals"

import {
  useGoalsManagement,
  MONTHS,
  type UserGoal,
} from"./use-goals-management"

interface GoalsMgmtUser {
  id: string
  name: string
  email?: string
  role?: string
  department?: string
  isActive?: boolean
  avatar?: string
}

interface GoalsManagementProps {
  users: GoalsMgmtUser[]
  onGoalUpdate: (userId: string, goals: UserGoal[]) => void
}

export function GoalsManagement({ users, onGoalUpdate }: GoalsManagementProps) {
  const t = useTranslations("settings")
  const { state, actions } = useGoalsManagement(users, onGoalUpdate)
  const {
    selectedUser, showTemplates, showCustomGoal, editingGoal, searchTerm,
    filterCategory, filterPeriod, isLoading, isSaving, error,
    successMessage, userGoalsMap, selectedTemplateIds, templateApplyMode,
    deleteConfirmGoal, isDeleting, editingTemplate, templateOverrides, hiddenTemplates,
    selectedYear, collapsedGoals, monthlyGoals, showApplyAllModal, applyAllValue,
    applyAllMonths, applyAllUsers, templateUsersMap, customGoalForm,
    filteredTemplates, activeTemplatesWithUsers, goalStats
  } = state
  const {
    setSelectedUser, setShowTemplates, setShowCustomGoal, setEditingGoal,
    setSearchTerm, setFilterCategory, setFilterPeriod, setSelectedTemplateIds,
    setTemplateApplyMode, setDeleteConfirmGoal, setEditingTemplate, setTemplateOverrides,
    setHiddenTemplates, setSelectedYear, setCollapsedGoals, setShowApplyAllModal,
    setApplyAllValue, setApplyAllMonths, setApplyAllUsers, setCustomGoalForm,
    getMonthlyValue, calculateRowTotal, calculateColumnTotal, calculateGrandTotal,
    getEffectiveTemplate, isTemplateAppliedToUser, getUserById,
    setMonthlyValue, applyValueToAll, toggleGoalCollapse, toggleTemplateSelection,
    handleApplySelectedTemplates, handleCreateCustomGoal,
    handleUpdateGoal, confirmDeleteGoal, handleAddUserToTemplate
  } = actions

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-4 py-3 rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {successMessage && (
        <div className="bg-status-success/10 border border-status-success/30 text-status-success px-4 py-3 rounded-xl flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          {successMessage}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h3 className={`${textStyles.titleLarge} flex items-center gap-2`}>
              <Target className="w-5 h-5 text-lia-text-primary" />
              {t("goals.title", { year: selectedYear })}
            </h3>
            <p className={textStyles.description}>
              {t("goals.description")}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedYear.toString()} onValueChange={(val) => setSelectedYear(parseInt(val))}>
            <SelectTrigger className="w-24 h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024">2024</SelectItem>
              <SelectItem value="2025">2025</SelectItem>
              <SelectItem value="2026">2026</SelectItem>
            </SelectContent>
          </Select>
          <Button 
            variant="outline" 
            onClick={() => setShowTemplates(true)} 
            className="gap-2 h-8 text-xs"
            disabled={users.length === 0 || isLoading}
          >
            <Plus className="w-3.5 h-3.5" />
            {t("goals.applyTemplate")}
          </Button>
          <Button 
            onClick={() => {
              setSelectedUser(users.length > 0 ? users[0] : null)
              setCustomGoalForm(prev => ({
                ...prev,
                userId: users.length > 0 ? users[0].id : ''
              }))
              setShowCustomGoal(true)
            }} 
            className="gap-2 h-8 text-xs bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            disabled={users.length === 0 || isLoading}
          >
            <Target className="w-3.5 h-3.5" />
            {t("goals.newGoal")}
          </Button>
        </div>
      </div>

      <GoalsStatsCards
        totalTemplates={goalStats.totalTemplates}
        totalAssigned={goalStats.totalAssigned}
        achieved={goalStats.achieved}
        inProgress={goalStats.inProgress}
        overdue={goalStats.overdue}
      />

      <Card className="border border-lia-border-subtle dark:border-lia-border-strong">
        <CardHeader className="py-3 dark:border-lia-border-strong">
          <CardTitle className={`${textStyles.h4} flex items-center justify-between`}>
            <span>{t("goals.goalsByCategory")}</span>
            {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          {users.length === 0 ? (
            <div className="text-center py-8 text-lia-text-primary">
              <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className={`${textStyles.titleLarge} mb-2`}>{t("goals.noUsersTitle")}</h3>
              <p className={textStyles.body}>{t("goals.noUsersDesc")}</p>
            </div>
          ) : activeTemplatesWithUsers.length === 0 ? (
            <div className="text-center py-8 text-lia-text-secondary">
              <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className={`${textStyles.titleLarge} mb-2 !text-lia-text-primary`}>{t("goals.noGoalsTitle")}</h3>
              <p className={`${textStyles.body} mb-4`}>
                {t("goals.noGoalsDesc")}
              </p>
              <Button 
                onClick={() => setShowTemplates(true)}
                className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
              >
                <Plus className="w-4 h-4" />
                {t("goals.applyTemplate")}
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {activeTemplatesWithUsers.map((template) => {
                const isCollapsed = collapsedGoals.has(template.id)
                const assignedUserObjects = template.assignedUsers
                  .map(uid => getUserById(uid))
                  .filter(Boolean)

                return (
                  <div key={template.id} className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl overflow-hidden">
                    <div 
                      className="flex items-center justify-between p-3 cursor-pointer hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none bg-lia-bg-secondary/50"
                      onClick={() => toggleGoalCollapse(template.id)}
                    >
                      <div className="flex items-center gap-2 flex-1">
                        {isCollapsed ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronUp className="w-3.5 h-3.5" />
                        )}
                        {getCategoryIcon(template.category)}
                        <div>
                          <h4 className={`${textStyles.label} !text-lia-text-primary dark:!text-lia-text-disabled`}>
                            {template.name}
                          </h4>
                          <p className={textStyles.caption}>
                            {template.description}
                          </p>
                        </div>
                        <Badge className={`text-micro ml-2 ${getCategoryColor(template.category)}`}>
                          {template.category}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-micro gap-1"
                          onClick={() => {
                            setShowApplyAllModal(template.id)
                            const effectiveTemplate = getEffectiveTemplate(template)
                            setApplyAllValue(effectiveTemplate.defaultTarget)
                          }}
                        >
                          <Settings className="w-3 h-3" />
                          {t("goals.applyForAll")}
                        </Button>
                      </div>
                    </div>

                    {!isCollapsed && (
                      <div className="border-t border-lia-border-subtle bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/50">
                        <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
                              <th className="text-left p-2 min-w-[140px] sticky left-0 bg-lia-bg-secondary dark:bg-lia-bg-secondary font-medium text-lia-text-secondary border-r border-lia-border-subtle dark:border-lia-border-subtle">
                                {t("goals.userColumn")}
                              </th>
                              {MONTHS.map((month) => (
                                <th 
                                  key={month.num} 
                                  className="text-center p-2 min-w-10 text-lia-text-secondary font-medium"
                                >
                                  {month.short}
                                </th>
                              ))}
                              <th className="text-center p-2 min-w-[50px] font-semibold text-lia-text-primary">
                                {t("goals.totalColumn")}
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {assignedUserObjects.map((user) => (
                              <tr key={user!.id} className="dark:border-lia-border-strong hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover">
                                <td className="p-2 sticky left-0 bg-lia-bg-secondary dark:bg-lia-bg-secondary border-r border-lia-border-subtle dark:border-lia-border-subtle">
                                  <div className="flex items-center gap-2">
                                    <Avatar className="w-5 h-5">
                                      <AvatarImage src={user!.avatar} alt={user!.name} />
                                      <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary font-medium text-micro">
                                        {user!.name.split(' ').map((n: string) => n[0]).join('')}
                                      </AvatarFallback>
                                    </Avatar>

                                    <span className="font-medium text-xs text-lia-text-primary truncate">{user!.name}</span>
                                  </div>
                                </td>
                                {MONTHS.map((month) => (

                                  <td 
                                    key={month.num} 
                                    className="p-1 text-center"
                                  >

                                    <EditableCell
                                      value={getMonthlyValue(template.id, user!.id, month.num, selectedYear)}
                                      onChange={(value) => setMonthlyValue(template.id, user!.id, month.num, selectedYear, value)}
                                    />
                                  </td>
                                ))}
                                <td className="p-2 text-center font-semibold text-lia-text-primary">
                                  {calculateRowTotal(template.id, user!.id, selectedYear)}
                                </td>
                              </tr>
                            ))}
                            <tr className="border-t-2 border-lia-border-default dark:border-lia-border-default bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                              <td className="p-2 font-semibold text-lia-text-primary sticky left-0 bg-lia-bg-tertiary border-r border-lia-border-subtle">
                                {t("goals.teamTotal")}
                              </td>
                              {MONTHS.map((month) => (
                                <td 
                                  key={month.num} 
                                  className="p-2 text-center font-semibold text-lia-text-primary"
                                >
                                  {calculateColumnTotal(template.id, month.num, selectedYear, template.assignedUsers)}
                                </td>
                              ))}
                              <td className="p-2 text-center font-bold text-lia-text-primary">
                                {calculateGrandTotal(template.id, selectedYear, template.assignedUsers)}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                        </div>
                        <div className="p-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAddUserToTemplate(template.id)}
                            className="text-micro h-6 gap-1.5 rounded-xl text-lia-text-primary border-lia-border-default hover:bg-lia-bg-tertiary"
                            disabled={isSaving}
                          >
                            <Plus className="w-3 h-3" />
                            {t("goals.addUser")}
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {showApplyAllModal && (
        <ApplyAllModal
          templateId={showApplyAllModal}
          applyAllValue={applyAllValue}
          applyAllMonths={applyAllMonths}
          applyAllUsers={applyAllUsers}
          isSaving={isSaving}
          setApplyAllValue={setApplyAllValue}
          setApplyAllMonths={setApplyAllMonths}
          setApplyAllUsers={setApplyAllUsers}
          setShowApplyAllModal={setShowApplyAllModal}
          applyValueToAll={applyValueToAll}
        />
      )}

      {showTemplates && (
        <GoalsTemplatesModal
          users={users}
          selectedUser={selectedUser}
          searchTerm={searchTerm}
          filterCategory={filterCategory}
          filterPeriod={filterPeriod}
          isSaving={isSaving}
          selectedTemplateIds={selectedTemplateIds}
          templateApplyMode={templateApplyMode}
          hiddenTemplates={hiddenTemplates}
          filteredTemplates={filteredTemplates}
          userGoalsMap={userGoalsMap}
          setSearchTerm={setSearchTerm}
          setFilterCategory={setFilterCategory}
          setFilterPeriod={setFilterPeriod}
          setSelectedTemplateIds={setSelectedTemplateIds}
          setTemplateApplyMode={setTemplateApplyMode}
          setHiddenTemplates={setHiddenTemplates}
          setShowTemplates={setShowTemplates}
          setEditingTemplate={setEditingTemplate}
          isTemplateAppliedToUser={isTemplateAppliedToUser}
          toggleTemplateSelection={toggleTemplateSelection}
          handleApplySelectedTemplates={handleApplySelectedTemplates}
        />
      )}

      {showCustomGoal && (
        <GoalsCustomGoalModal
          users={users}
          selectedUser={selectedUser}
          customGoalForm={customGoalForm}
          isSaving={isSaving}
          setSelectedUser={setSelectedUser}
          setShowCustomGoal={setShowCustomGoal}
          setCustomGoalForm={setCustomGoalForm}
          handleCreateCustomGoal={handleCreateCustomGoal}
        />
      )}

      {editingGoal && (
        <GoalsEditGoalModal
          editingGoal={editingGoal}
          isSaving={isSaving}
          setEditingGoal={setEditingGoal}
          handleUpdateGoal={handleUpdateGoal}
        />
      )}

      {deleteConfirmGoal && (
        <DeleteConfirmModal
          goal={deleteConfirmGoal}
          isDeleting={isDeleting}
          onCancel={() => setDeleteConfirmGoal(null)}
          onConfirm={confirmDeleteGoal}
        />
      )}

      {editingTemplate && (
        <GoalsEditTemplateModal
          editingTemplate={editingTemplate}
          setEditingTemplate={setEditingTemplate}
          setTemplateOverrides={setTemplateOverrides}
        />
      )}
    </div>
  )
}
