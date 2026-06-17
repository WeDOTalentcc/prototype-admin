import { CandidateList } from "@/services/lia-api"

export interface SharedSearch {
  id: string
  share_type: 'search' | 'list'
  title: string
  candidate_count: number
  recipient_email: string
  recipient_name?: string | null
  share_url: string
  status: 'active' | 'expired' | 'revoked'
  first_accessed_at?: string | null
  created_at: string
  expires_at?: string | null
  feedback_counts: {
    approved: number
    rejected: number
    maybe: number
    pending: number
    new_count: number
  }
}

export interface ListsTabProps {
  onListSelect: (listId: string) => void
  onAddToJobs: (listId: string) => void
  onGoToSearch?: () => void
  onAddCandidateToList?: (listId: string, listName: string) => void
  onViewSharedDetails?: (id: string) => void
}

export interface ListCardProps {
  list: CandidateList
  onSelect: (listId: string) => void
  onEdit: (list: CandidateList) => void
  onDelete: (list: CandidateList) => void
  onAddToJobs: (listId: string) => void
  onAddCandidate: (list: CandidateList) => void
  onShare: (list: CandidateList) => void
}

export interface SharedSearchesSectionProps {
  sharedSearches: SharedSearch[]
  loadingShared: boolean
  totalNewFeedbacks: number
  onViewDetails: (id: string) => void
  onCopyLink: (shareUrl: string) => void
  onResendInvite: (id: string) => void
  onRevokeShare: (id: string) => void
}

export interface ListFormModalProps {
  open: boolean
  editingList: CandidateList | null
  formName: string
  formDescription: string
  formColor: string
  saving: boolean
  onFormNameChange: (value: string) => void
  onFormDescriptionChange: (value: string) => void
  onFormColorChange: (value: string) => void
  onSave: () => void
  onClose: () => void
}

export interface DeleteListDialogProps {
  listToDelete: CandidateList | null
  deleting: boolean
  onDelete: () => void
  onCancel: () => void
}

export function formatDate(dateString: string | null) {
  if (!dateString) return 'Não disponível'
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

export function truncateText(text: string, maxLength: number = 80) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trim() + '...'
}
