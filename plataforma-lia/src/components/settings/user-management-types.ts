export interface UserData {
  id: string
  name: string
  email: string
  phone: string
  whatsapp: string
  role: string
  department: string
  position: string
  avatar?: string
  status: 'ativo' | 'inativo' | 'pendente'
  permissions: string[]
  emailSignature: string
  location: string
  hireDate: string
  isManager: boolean
  managerId?: string
  teamMembers?: string[]
  lastLogin?: string
  createdAt: string
  updatedAt: string
  isScimManaged?: boolean
}

export interface UserManagementProps {
  onUserUpdate?: (user: UserData) => void
}
