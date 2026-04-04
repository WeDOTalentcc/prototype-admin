import { useState, useCallback, useRef, useEffect } from 'react'
import { useChatStateStore } from '@/stores/chat-state-store'

export type ChatContext = 'general' | 'wizard' | 'fast_track'

export interface WizardSnapshot {
  stage: string
  basicInfoFields: Record<string, unknown>
  technicalSkills: unknown[]
  behavioralCompetencies: unknown[]
  salaryInfo: Record<string, unknown>
  wsiQuestions: unknown[]
  detectedCriteria: Record<string, unknown>
  generatedJobDescription: string
  fastTrackSourceJobId: string | null
  timestamp: number
}

export interface GeneralChatSnapshot {
  conversationId: string | null
  lastMessageIndex: number
  timestamp: number
}

export interface ContextSwitchingState {
  currentContext: ChatContext
  previousContext: ChatContext | null
  wizardSnapshot: WizardSnapshot | null
  generalSnapshot: GeneralChatSnapshot | null
  switchCount: number
  canSwitchToWizard: boolean
  canSwitchToGeneral: boolean
}

export interface UseContextSwitchingOptions {
  onContextSwitch?: (from: ChatContext, to: ChatContext) => void
  onWizardRestore?: (snapshot: WizardSnapshot) => void
  onGeneralRestore?: (snapshot: GeneralChatSnapshot) => void
  autoDetectIntent?: boolean
}

export interface UseContextSwitchingReturn {
  state: ContextSwitchingState
  currentContext: ChatContext
  isInWizardContext: boolean
  isInGeneralContext: boolean
  switchToWizard: (snapshot?: Partial<WizardSnapshot>) => void
  switchToGeneral: (snapshot?: Partial<GeneralChatSnapshot>) => void
  switchToFastTrack: () => void
  saveWizardSnapshot: (data: Partial<WizardSnapshot>) => void
  saveGeneralSnapshot: (data: Partial<GeneralChatSnapshot>) => void
  restoreWizardSnapshot: () => WizardSnapshot | null
  restoreGeneralSnapshot: () => GeneralChatSnapshot | null
  detectContextFromMessage: (message: string) => ChatContext | null
  clearSnapshots: () => void
  syncContext: (wizardMode: string) => void
}

const WIZARD_INTENT_PATTERNS = [
  /criar\s+(nova\s+)?vaga/i,
  /abrir\s+(nova\s+)?posi[çc][aã]o/i,
  /nova\s+vaga/i,
  /publicar\s+vaga/i,
  /começar\s+wizard/i,
  /voltar\s+(para\s+)?o?\s*wizard/i,
  /continuar\s+(a\s+)?vaga/i,
  /retomar\s+(a\s+)?cria[çc][aã]o/i,
]

const GENERAL_INTENT_PATTERNS = [
  /ajuda\s+com/i,
  /como\s+(eu\s+)?(fa[çc]o|posso)/i,
  /me\s+explica/i,
  /o\s+que\s+[eé]/i,
  /quero\s+conversar/i,
  /tenho\s+uma\s+d[uú]vida/i,
  /analis(e|ar)\s+candidato/i,
  /buscar?\s+candidato/i,
  /comparar?\s+(candidatos|vagas)/i,
  /relat[oó]rio/i,
  /pausar\s+(o\s+)?wizard/i,
  /sair\s+d(o|a)\s+(wizard|cria[çc][aã]o)/i,
]

const FAST_TRACK_INTENT_PATTERNS = [
  /fast\s*track/i,
  /usar\s+vaga\s+anterior/i,
  /reaproveitar\s+vaga/i,
  /copiar\s+vaga/i,
  /vaga\s+similar/i,
  /duplicar\s+vaga/i,
]

function loadStoredSnapshots(): { wizard: WizardSnapshot | null; general: GeneralChatSnapshot | null } {
  try {
    const stored = useChatStateStore.getState().contextSnapshots
    const now = Date.now()
    const maxAge = 24 * 60 * 60 * 1000

    return {
      wizard: stored.wizard && (now - stored.wizard.timestamp) < maxAge ? stored.wizard as unknown as WizardSnapshot : null,
      general: stored.general && (now - stored.general.timestamp) < maxAge ? stored.general as unknown as GeneralChatSnapshot : null,
    }
  } catch {
  }
  return { wizard: null, general: null }
}

function saveStoredSnapshots(wizard: WizardSnapshot | null, general: GeneralChatSnapshot | null): void {
  try {
    useChatStateStore.getState().setContextSnapshots({
      wizard: wizard as unknown as import('@/stores/chat-state-store').StoredWizardSnapshot | null,
      general: general as unknown as import('@/stores/chat-state-store').StoredGeneralChatSnapshot | null,
    })
  } catch {
  }
}

export function useContextSwitching(options: UseContextSwitchingOptions = {}): UseContextSwitchingReturn {
  const { onContextSwitch, onWizardRestore, onGeneralRestore, autoDetectIntent = true } = options

  const [currentContext, setCurrentContext] = useState<ChatContext>('general')
  const [previousContext, setPreviousContext] = useState<ChatContext | null>(null)
  const [switchCount, setSwitchCount] = useState(0)
  
  const wizardSnapshotRef = useRef<WizardSnapshot | null>(null)
  const generalSnapshotRef = useRef<GeneralChatSnapshot | null>(null)

  useEffect(() => {
    const stored = loadStoredSnapshots()
    wizardSnapshotRef.current = stored.wizard
    generalSnapshotRef.current = stored.general
  }, [])

  const saveWizardSnapshot = useCallback((data: Partial<WizardSnapshot>) => {
    const snapshot: WizardSnapshot = {
      stage: data.stage || 'input-evaluation',
      basicInfoFields: data.basicInfoFields || {},
      technicalSkills: data.technicalSkills || [],
      behavioralCompetencies: data.behavioralCompetencies || [],
      salaryInfo: data.salaryInfo || {},
      wsiQuestions: data.wsiQuestions || [],
      detectedCriteria: data.detectedCriteria || {},
      generatedJobDescription: data.generatedJobDescription || '',
      fastTrackSourceJobId: data.fastTrackSourceJobId || null,
      timestamp: Date.now(),
    }
    wizardSnapshotRef.current = snapshot
    saveStoredSnapshots(snapshot, generalSnapshotRef.current)
  }, [])

  const saveGeneralSnapshot = useCallback((data: Partial<GeneralChatSnapshot>) => {
    const snapshot: GeneralChatSnapshot = {
      conversationId: data.conversationId || null,
      lastMessageIndex: data.lastMessageIndex || 0,
      timestamp: Date.now(),
    }
    generalSnapshotRef.current = snapshot
    saveStoredSnapshots(wizardSnapshotRef.current, snapshot)
  }, [])

  const switchToWizard = useCallback((snapshot?: Partial<WizardSnapshot>) => {
    if (currentContext === 'wizard') return

    if (currentContext === 'general' && generalSnapshotRef.current === null) {
      saveGeneralSnapshot({ lastMessageIndex: 0 })
    }

    const previousCtx = currentContext
    setPreviousContext(previousCtx)
    setCurrentContext('wizard')
    setSwitchCount(prev => prev + 1)

    if (snapshot) {
      saveWizardSnapshot(snapshot)
    }

    onContextSwitch?.(previousCtx, 'wizard')

    if (wizardSnapshotRef.current && onWizardRestore) {
      onWizardRestore(wizardSnapshotRef.current)
    }
  }, [currentContext, onContextSwitch, onWizardRestore, saveGeneralSnapshot, saveWizardSnapshot])

  const switchToGeneral = useCallback((snapshot?: Partial<GeneralChatSnapshot>) => {
    if (currentContext === 'general') return

    if ((currentContext === 'wizard' || currentContext === 'fast_track') && wizardSnapshotRef.current === null) {
      saveWizardSnapshot({ stage: 'input-evaluation' })
    }

    const previousCtx = currentContext
    setPreviousContext(previousCtx)
    setCurrentContext('general')
    setSwitchCount(prev => prev + 1)

    if (snapshot) {
      saveGeneralSnapshot(snapshot)
    }

    onContextSwitch?.(previousCtx, 'general')

    if (generalSnapshotRef.current && onGeneralRestore) {
      onGeneralRestore(generalSnapshotRef.current)
    }
  }, [currentContext, onContextSwitch, onGeneralRestore, saveGeneralSnapshot, saveWizardSnapshot])

  const switchToFastTrack = useCallback(() => {
    if (currentContext === 'fast_track') return

    const previousCtx = currentContext
    setPreviousContext(previousCtx)
    setCurrentContext('fast_track')
    setSwitchCount(prev => prev + 1)

    onContextSwitch?.(previousCtx, 'fast_track')
  }, [currentContext, onContextSwitch])

  const restoreWizardSnapshot = useCallback((): WizardSnapshot | null => {
    return wizardSnapshotRef.current
  }, [])

  const restoreGeneralSnapshot = useCallback((): GeneralChatSnapshot | null => {
    return generalSnapshotRef.current
  }, [])

  const detectContextFromMessage = useCallback((message: string): ChatContext | null => {
    if (!autoDetectIntent) return null

    const normalizedMessage = message.trim().toLowerCase()

    for (const pattern of FAST_TRACK_INTENT_PATTERNS) {
      if (pattern.test(normalizedMessage)) {
        return 'fast_track'
      }
    }

    for (const pattern of WIZARD_INTENT_PATTERNS) {
      if (pattern.test(normalizedMessage)) {
        return 'wizard'
      }
    }

    for (const pattern of GENERAL_INTENT_PATTERNS) {
      if (pattern.test(normalizedMessage)) {
        return 'general'
      }
    }

    return null
  }, [autoDetectIntent])

  const clearSnapshots = useCallback(() => {
    wizardSnapshotRef.current = null
    generalSnapshotRef.current = null
    useChatStateStore.getState().clearContextSnapshots()
  }, [])

  // Use ref for currentContext to keep syncContext callback stable
  // This prevents infinite loops when syncContext is used as a useEffect dependency
  const currentContextRef = useRef(currentContext)
  currentContextRef.current = currentContext
  
  // Also use refs for optional callbacks to keep syncContext stable
  const onContextSwitchRef = useRef(onContextSwitch)
  const onWizardRestoreRef = useRef(onWizardRestore)
  const onGeneralRestoreRef = useRef(onGeneralRestore)
  onContextSwitchRef.current = onContextSwitch
  onWizardRestoreRef.current = onWizardRestore
  onGeneralRestoreRef.current = onGeneralRestore
  
  const syncContext = useCallback((wizardMode: string, options?: { skipCallbacks?: boolean; skipSnapshotRestore?: boolean }) => {
    let targetContext: ChatContext
    if (wizardMode === 'general') {
      targetContext = 'general'
    } else if (wizardMode === 'fast_track') {
      targetContext = 'fast_track'
    } else {
      targetContext = 'wizard'
    }
    
    // Only sync if context has actually changed - use ref to avoid dependency
    if (currentContextRef.current === targetContext) {
      return
    }

    const previousCtx = currentContextRef.current
    setPreviousContext(previousCtx)
    setCurrentContext(targetContext)
    setSwitchCount(prev => prev + 1)

    // Call onContextSwitch callback unless explicitly skipped
    if (!options?.skipCallbacks) {
      onContextSwitchRef.current?.(previousCtx, targetContext)
    }

    // Optionally restore snapshots unless explicitly skipped
    if (!options?.skipSnapshotRestore) {
      if (targetContext === 'wizard' && wizardSnapshotRef.current && onWizardRestoreRef.current) {
        onWizardRestoreRef.current(wizardSnapshotRef.current)
      } else if (targetContext === 'general' && generalSnapshotRef.current && onGeneralRestoreRef.current) {
        onGeneralRestoreRef.current(generalSnapshotRef.current)
      }
    }
  }, []) // Empty deps - uses refs for all state/callback access

  const state: ContextSwitchingState = {
    currentContext,
    previousContext,
    wizardSnapshot: wizardSnapshotRef.current,
    generalSnapshot: generalSnapshotRef.current,
    switchCount,
    canSwitchToWizard: currentContext !== 'wizard',
    canSwitchToGeneral: currentContext !== 'general',
  }

  return {
    state,
    currentContext,
    isInWizardContext: currentContext === 'wizard' || currentContext === 'fast_track',
    isInGeneralContext: currentContext === 'general',
    switchToWizard,
    switchToGeneral,
    switchToFastTrack,
    saveWizardSnapshot,
    saveGeneralSnapshot,
    restoreWizardSnapshot,
    restoreGeneralSnapshot,
    detectContextFromMessage,
    clearSnapshots,
    syncContext,
  }
}
