import { useLiaFloat } from '@/contexts/lia-float-context'

export interface LiaEntityTarget {
  type: 'candidate' | 'job'
  id: string
  name: string
  meta?: Record<string, unknown>
}

export function useLiaEntitySelection() {
  const { openWithEntity } = useLiaFloat()

  const openEntityChat = (target: LiaEntityTarget) => {
    openWithEntity({ type: target.type, id: target.id, name: target.name, meta: target.meta })
  }

  return { openEntityChat }
}
