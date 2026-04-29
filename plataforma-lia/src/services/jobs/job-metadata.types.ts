export interface RemoteOption {
  id: string | number
  name: string
  description?: string
  code?: string
}

export interface SeniorityOption extends RemoteOption {
  level?: number
}

export interface UserSearchHit {
  id: string | number
  name: string
  email: string
  role?: string | null
  avatar?: string | null
}

export interface JsonApiList<T> {
  data: T[]
  meta?: { total?: number }
}
