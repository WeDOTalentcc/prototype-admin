"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Edit, Trash2, Mail, MapPin, Users, Shield, Loader2, Send
} from "lucide-react"
import { textStyles, badgeStyles } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import type { UserData } from "./user-management-types"
import { useTranslations } from "next-intl"

// Override de tamanho aplicado em cima do `getStatusColor()` para que as
// pílulas do card de usuário fiquem na mesma densidade compacta da tabela
// (texto micro, padding mínimo, peso normal). Sem isso, o `badgeStyles.*`
// reaplica `px-2 py-0.5 text-micro font-medium`, inflando a badge no card.
const COMPACT_STATUS_OVERRIDE = "px-1.5 py-0 text-[10px] leading-[14px] font-normal"

interface UserListProps {
  filteredUsers: UserData[]
  viewMode: "cards" | "table"
  isSCIMEnabled: boolean
  resendingInvite: string | null
  getStatusColor: (status: string) => string
  onEditUser: (user: UserData) => void
  onDeleteUser: (userId: string) => void
  onResendInvitation: (userId: string, userEmail: string) => void
}

export function UserList({
  filteredUsers,
  viewMode,
  isSCIMEnabled,
  resendingInvite,
  getStatusColor,
  onEditUser,
  onDeleteUser,
  onResendInvitation,
}: UserListProps) {
  const t = useTranslations("settings.users")

  if (filteredUsers.length === 0) {
    return (
      <Card className="rounded-md">
        <CardContent className="p-4 text-center">
          <div className="text-lia-text-secondary">
            <Users className="w-10 h-10 mx-auto mb-3 opacity-50" />
            <h3 className={textStyles.subtitle}>{t("noUsersFound")}</h3>
            <p className={textStyles.description + " mt-1"}>{t("noUsersHint")}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (viewMode === "cards") {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="users-list-cards">
        {filteredUsers.map((user) => (
          <Card key={user.id} data-testid={`user-card-${user.id}`} className="rounded-xl hover:transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Avatar className="w-9 h-9">
                    <AvatarImage src={user.avatar} alt={t("avatarOf", { name: user.name })} />
                    <AvatarFallback className={`${badgeStyles.info} font-medium text-micro`}>
                      {user.name.split(" ").map(n => n[0]).join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h4 className={cn(textStyles.subtitle, "leading-tight")}>{user.name}</h4>
                    <p className={cn(textStyles.description, "leading-tight")}>{user.role}</p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <Chip variant="neutral" muted density="compact" className={cn(getStatusColor(user.status), COMPACT_STATUS_OVERRIDE)}>
                        {user.status === "active" ? t("statusActive") : user.status === "inactive" ? t("statusInactive") : t("statusPending")}
                      </Chip>
                      {user.isScimManaged && (
                        <Chip variant="neutral" muted density="compact" className={cn("bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle", COMPACT_STATUS_OVERRIDE)}>
                          <Shield className="w-2.5 h-2.5 mr-0.5" />
                          SSO
                        </Chip>
                      )}
                    </div>
                  </div>
                </div>
                {!isSCIMEnabled && (
                  <div className="flex items-center gap-0.5">
                    <Button
                      data-testid={`user-card-edit-${user.id}`}
                      variant="ghost"
                      size="sm"
                      onClick={() => onEditUser(user)}
                      className="h-7 w-7 p-0"
                      title={t("editTooltip")}
                    >
                      <Edit className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      data-testid={`user-card-delete-${user.id}`}
                      variant="ghost"
                      size="sm"
                      onClick={() => onDeleteUser(user.id)}
                      className="h-7 w-7 p-0 text-status-error dark:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/30"
                      title={t("deleteTooltip")}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-3 text-micro text-lia-text-secondary">
                  <span className="flex items-center gap-1">
                    <Mail className="w-3 h-3" />
                    {user.email}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {user.location}
                  </span>
                </div>

                {user.isManager && (
                  <Chip variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary border border-lia-border-subtle dark:border-lia-border-subtle text-micro">
                    <Users className="w-3 h-3 mr-1" />
                    {t("manager")}
                  </Chip>
                )}

                {user.status === "inactive" && (
                  <Button
                    data-testid={`user-resend-invite-${user.id}`}
                    variant="outline"
                    size="sm"
                    onClick={() => onResendInvitation(user.id, user.email)}
                    disabled={resendingInvite === user.id}
                    className="w-full mt-1.5 text-micro gap-1.5 h-7"
                  >
                    {resendingInvite === user.id ? (
                      <>
                        <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                        {t("sending")}
                      </>
                    ) : (
                      <>
                        <Send className="w-3 h-3" />
                        {t("resendInvite")}
                      </>
                    )}
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <Card data-testid="users-list-table" className="rounded-md">
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-lia-bg-secondary dark:bg-lia-bg-secondary">
              <tr>
                <th className="px-2 py-2.5 text-left text-micro font-medium text-lia-text-secondary uppercase tracking-wider">
                  {t("tableUser")}
                </th>
                <th className="px-2 py-2.5 text-left text-micro font-medium text-lia-text-secondary uppercase tracking-wider">
                  {t("tableRole")}
                </th>
                <th className="px-2 py-2.5 text-left text-micro font-medium text-lia-text-secondary uppercase tracking-wider">
                  {t("tableStatus")}
                </th>
                {!isSCIMEnabled && (
                  <th className="px-2 py-2.5 text-center text-micro font-medium text-lia-text-secondary uppercase tracking-wider">
                    {t("tableActions")}
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-lia-bg-primary dark:bg-lia-bg-secondary divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
              {filteredUsers.map((user) => (
                <tr key={user.id} data-testid={`user-row-${user.id}`} className="hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse">
                  <td className="px-2 py-1.5 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={user.avatar} alt={t("avatarOf", { name: user.name })} />
                        <AvatarFallback className={`${badgeStyles.info} font-medium text-micro`}>
                          {user.name.split(" ").map(n => n[0]).join("")}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <div className={textStyles.subtitle}>{user.name}</div>
                        <div className={textStyles.description}>{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-2 py-1.5 whitespace-nowrap">
                    <div className={textStyles.subtitle}>{user.role}</div>
                    <div className={textStyles.description}>{user.department}</div>
                  </td>
                  <td className="px-2 py-1.5 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <Chip variant="neutral" muted className={`${getStatusColor(user.status)} text-micro`}>
                        {user.status === "active" ? t("statusActive") : user.status === "inactive" ? t("statusInactive") : t("statusPending")}
                      </Chip>
                      {user.isScimManaged && (
                        <Chip variant="neutral" muted className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary border-lia-border-subtle dark:border-lia-border-subtle text-micro">
                          <Shield className="w-2.5 h-2.5 mr-0.5" />
                          SSO
                        </Chip>
                      )}
                    </div>
                  </td>
                  {!isSCIMEnabled && (
                    <td className="px-2 py-1.5 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Button
                          data-testid={`user-row-edit-${user.id}`}
                          variant="ghost"
                          size="sm"
                          onClick={() => onEditUser(user)}
                          className="h-7 w-7 p-0"
                          title={t("editTooltip")}
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          data-testid={`user-row-delete-${user.id}`}
                          variant="ghost"
                          size="sm"
                          onClick={() => onDeleteUser(user.id)}
                          className="h-7 w-7 p-0 text-status-error dark:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/30"
                          title={t("deleteTooltip")}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
