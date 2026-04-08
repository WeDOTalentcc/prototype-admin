import re
import os

base = '/home/runner/workspace/plataforma-lia/src'

def read(path):
    with open(path) as f:
        return f.read()

def write(path, content):
    with open(path, 'w') as f:
        f.write(content)

def fix(path, old, new, label=""):
    content = read(path)
    if old in content:
        content = content.replace(old, new)
        write(path, content)
        print(f"  FIXED {label}: {os.path.basename(path)}")
        return True
    else:
        print(f"  MISS {label}: {os.path.basename(path)}")
        return False

# ===== 1. multimodal-upload.tsx =====
# analyzeFile missing - it's a regular async function, wrap in useCallback
path = f'{base}/components/chat/multimodal-upload.tsx'
content = read(path)
original = content

# Change: const analyzeFile = async (fileToAnalyze?: File) => { ... }
# To: const analyzeFile = useCallback(async (fileToAnalyze?: File) => { ... }, [onAnalysisComplete, onError, analysisType])
# First check imports
if 'useCallback' not in content:
    content = content.replace(
        'import React, { useState, useRef, useCallback }',
        'import React, { useState, useRef, useCallback }'
    )
    # Already has useCallback from import

# The analyzeFile function ends before const clearFile
old_fn = '  const analyzeFile = async (fileToAnalyze?: File) => {'
new_fn = '  const analyzeFile = useCallback(async (fileToAnalyze?: File) => {'

# Find end of analyzeFile function
idx_start = content.find(old_fn)
if idx_start != -1:
    # Find the closing } of analyzeFile
    idx_end = content.find('\n  const clearFile', idx_start)
    if idx_end != -1:
        fn_body = content[idx_start:idx_end]
        new_fn_body = fn_body.replace(
            '  const analyzeFile = async (fileToAnalyze?: File) => {',
            '  const analyzeFile = useCallback(async (fileToAnalyze?: File) => {'
        )
        # Add closing ) with deps
        new_fn_body = new_fn_body.rstrip() + '\n  }, [analysisType, onAnalysisComplete, onError])'
        content = content[:idx_start] + new_fn_body + '\n' + content[idx_end:]
        write(path, content)
        print(f"  FIXED analyzeFile useCallback: multimodal-upload.tsx")
    else:
        print(f"  MISS analyzeFile end: multimodal-upload.tsx")
else:
    print(f"  MISS analyzeFile: multimodal-upload.tsx")

# ===== 2. voice-chat-button.tsx =====
# processAudio missing - it's an async function, wrap in useCallback
path = f'{base}/components/chat/voice-chat-button.tsx'
content = read(path)
original = content

old_fn = '  const processAudio = async (audioBlob: Blob) => {'
idx_start = content.find(old_fn)
if idx_start != -1:
    idx_end = content.find('\n  const playAudioResponse', idx_start)
    if idx_end != -1:
        fn_body = content[idx_start:idx_end]
        new_fn_body = fn_body.replace(
            '  const processAudio = async (audioBlob: Blob) => {',
            '  const processAudio = useCallback(async (audioBlob: Blob) => {'
        )
        new_fn_body = new_fn_body.rstrip() + '\n  }, [onError, onResponse, onTranscription, sessionId])'
        content = content[:idx_start] + new_fn_body + '\n' + content[idx_end:]
        write(path, content)
        print(f"  FIXED processAudio useCallback: voice-chat-button.tsx")
    else:
        print(f"  MISS processAudio end: voice-chat-button.tsx")
        # Try different end marker
        idx_end2 = content.find('\n  const playAudio', idx_start)
        if idx_end2 != -1:
            print(f"  Found alternative end at {idx_end2}")
else:
    print(f"  MISS processAudio: voice-chat-button.tsx")

# Check if useCallback is imported
content = read(path)
if 'useCallback' not in content:
    content = content.replace(
        'import { useState, useRef, useCallback }',
        'import { useState, useRef, useCallback }'
    )
    print("voice-chat-button useCallback import check ok")

# ===== 3. useExpandedChatCoreHooks.ts =====
# resolvedCompanyId missing at line 271, setMessages missing at line 298
path = f'{base}/components/expanded-chat/hooks/useExpandedChatCoreHooks.ts'
content = read(path)

# Line 271: useEffect that has fetchWizardSuggestions - missing resolvedCompanyId
# From code: [detectedCriteria?.cargo, detectedCriteria?.departamento, mode, fetchWizardSuggestions]
fix(path,
    '  }, [detectedCriteria?.cargo, detectedCriteria?.departamento, mode, fetchWizardSuggestions])',
    '  }, [detectedCriteria?.cargo, detectedCriteria?.departamento, mode, fetchWizardSuggestions, resolvedCompanyId])',
    'resolvedCompanyId dep'
)

# Line 298: setMessages missing - from the effect at line 281 which has setMessages and setFastTrackMessageSent etc
# deps are: [fastTrackHasSuggestions, fastTrackSuggestions, fastTrackMessageSent, mode, currentStage, analytics, fastTrackSuggestionsShownTracked, getFastTrackLiaMessage, setFastTrackMessageSent, setFastTrackSuggestionsShownTracked]
content = read(path)
if 'setMessages' not in content[content.find('[fastTrackHasSuggestions'):content.find('])', content.find('[fastTrackHasSuggestions'))+200]:
    fix(path,
        '  }, [fastTrackHasSuggestions, fastTrackSuggestions, fastTrackMessageSent, mode, currentStage, analytics, fastTrackSuggestionsShownTracked, getFastTrackLiaMessage, setFastTrackMessageSent, setFastTrackSuggestionsShownTracked])',
        '  }, [fastTrackHasSuggestions, fastTrackSuggestions, fastTrackMessageSent, mode, currentStage, analytics, fastTrackSuggestionsShownTracked, getFastTrackLiaMessage, setFastTrackMessageSent, setFastTrackSuggestionsShownTracked, setMessages])',
        'setMessages dep'
    )
else:
    print("  setMessages already in deps")

# ===== 4. useExpandedChatEffects.ts =====
# resolvedTenantId missing at line 349
path = f'{base}/components/expanded-chat/hooks/useExpandedChatEffects.ts'
fix(path,
    '  }, [user, proactiveActionIds, setMessages, setProactiveActionIds])',
    '  }, [user, proactiveActionIds, setMessages, setProactiveActionIds, resolvedTenantId])',
    'resolvedTenantId dep'
)

# ===== 5. useExpandedChatProactiveHandlers.ts =====
# basicInfoFields missing at line 178 (salary benchmark effect)
# Current: [currentStage, basicInfoFields.cargo, basicInfoFields.area, basicInfoFields.localidade, detectedCriteria, salaryBenchmark, salaryInfo.maxSalary, salaryInfo.minSalary, setIsLoadingBenchmark, setSalaryBenchmark, setSalaryInfo]
# The linter says basicInfoFields is missing
path = f'{base}/components/expanded-chat/hooks/useExpandedChatProactiveHandlers.ts'
fix(path,
    '  }, [currentStage, basicInfoFields.cargo, basicInfoFields.area, basicInfoFields.localidade, detectedCriteria, salaryBenchmark, salaryInfo.maxSalary, salaryInfo.minSalary, setIsLoadingBenchmark, setSalaryBenchmark, setSalaryInfo])',
    '  }, [currentStage, basicInfoFields, detectedCriteria, salaryBenchmark, salaryInfo.maxSalary, salaryInfo.minSalary, setIsLoadingBenchmark, setSalaryBenchmark, setSalaryInfo])',
    'basicInfoFields dep'
)

# ===== 6. useExpandedChatWiring.ts =====
# state missing at line 291
path = f'{base}/components/expanded-chat/hooks/useExpandedChatWiring.ts'
content = read(path)
lines = content.split('\n')
print(f"\nuseExpandedChatWiring.ts lines 285-300:")
for i, line in enumerate(lines[284:301], 285):
    print(f"  L{i}: {line}")

# ===== 7. useWizardState.ts =====
# setDraftId missing at line 261
path = f'{base}/components/expanded-chat/hooks/useWizardState.ts'
# resetWizard has []) but uses setDraftId
fix(path,
    '    setDraftId(null)\n  }, [])',
    '    setDraftId(null)\n  }, [setDraftId])',
    'setDraftId dep'
)

# ===== 8. SalaryStage.tsx =====
# salaryInfo missing in useMemo at line 137
path = f'{base}/components/expanded-chat/stages/SalaryStage.tsx'
content = read(path)
lines = content.split('\n')
print(f"\nSalaryStage.tsx lines 130-145:")
for i, line in enumerate(lines[129:146], 130):
    print(f"  L{i}: {line}")

# ===== 9. useLiaChatPanelState.ts =====
# handleSend missing: attachedCvFile, awaitingCandidateName, screenCv, setChatConversationId
path = f'{base}/components/lia-float/useLiaChatPanelState.ts'
content = read(path)
# Find the handleSend useCallback deps that are missing
# The current deps: [inputText, conversationId, isCreating, isStreaming, addMessage, initConversation, detectAction, detectIntent, openSplitView, wsSend, connectChat, setSharedConversationId, currentScope, contextDismissed, pendingCvFields, uploadedFileInfo, setPendingCvFields, setUploadedFileInfo, updateRecentItem]
old_deps = '    inputText, conversationId, isCreating, isStreaming,\n    addMessage, initConversation, detectAction, detectIntent,\n    openSplitView, wsSend, connectChat, setSharedConversationId, currentScope,\n    contextDismissed,\n    pendingCvFields, uploadedFileInfo, setPendingCvFields, setUploadedFileInfo,\n    updateRecentItem,\n  ])'
new_deps = '    inputText, conversationId, isCreating, isStreaming,\n    addMessage, initConversation, detectAction, detectIntent,\n    openSplitView, wsSend, connectChat, setSharedConversationId, currentScope,\n    contextDismissed,\n    pendingCvFields, uploadedFileInfo, setPendingCvFields, setUploadedFileInfo,\n    updateRecentItem,\n    attachedCvFile, awaitingCandidateName, screenCv, setChatConversationId,\n  ])'
if old_deps in content:
    content = content.replace(old_deps, new_deps)
    write(path, content)
    print(f"  FIXED handleSend missing deps: useLiaChatPanelState.ts")
else:
    print(f"  MISS handleSend deps: useLiaChatPanelState.ts")
    # Let's search for the pattern
    idx = content.find('updateRecentItem,\n  ])')
    if idx != -1:
        print(f"  Found updateRecentItem at idx {idx}")
        print(repr(content[idx:idx+50]))

# ===== 10. add-to-job-modal.tsx =====
# checkDuplicates changes on every render - wrap in useCallback
path = f'{base}/components/modals/add-to-job-modal.tsx'
content = read(path)
# The checkDuplicates function should be wrapped in useCallback
# Currently: const checkDuplicates = async (jobId: string) => {
# We added it to deps but now need to wrap it in useCallback
old = '  const checkDuplicates = async (jobId: string) => {'
new = '  const checkDuplicates = useCallback(async (jobId: string) => {'
if old in content:
    # Find end of checkDuplicates
    idx_start = content.find(old)
    # Find closing } - need to look for the function end
    # Look for next const/useEffect at top level
    idx_end = content.find('\n  const ', idx_start + 10)
    if idx_end == -1:
        idx_end = content.find('\n  useEffect(', idx_start + 10)
    if idx_end == -1:
        idx_end = content.find('\n  return (', idx_start + 10)
    
    if idx_end != -1:
        fn_body = content[idx_start:idx_end]
        # Replace function declaration
        new_fn = fn_body.replace(
            '  const checkDuplicates = async (jobId: string) => {',
            '  const checkDuplicates = useCallback(async (jobId: string) => {'
        )
        # The function body ends with }
        # Add closing useCallback args
        last_brace = new_fn.rfind('\n  }')
        if last_brace != -1:
            new_fn = new_fn[:last_brace + 4] + ', [jobs, effectiveCandidateIds, setDuplicateIds])'
        content = content[:idx_start] + new_fn + content[idx_end:]
        write(path, content)
        print(f"  FIXED checkDuplicates useCallback: add-to-job-modal.tsx")
    else:
        print(f"  MISS checkDuplicates end: add-to-job-modal.tsx")
else:
    # Maybe already wrapped
    if 'checkDuplicates = useCallback' in content:
        print(f"  checkDuplicates already wrapped")
    else:
        print(f"  MISS checkDuplicates: add-to-job-modal.tsx")
        # Show context
        idx = content.find('checkDuplicates')
        print(repr(content[idx:idx+100]))

# ===== 11. useJobStatusModal.ts =====
# jobs missing in useEffect (line 197), handleSubmitAndNavigate missing in useCallback (line 254)
path = f'{base}/components/modals/job-status/useJobStatusModal.ts'
content = read(path)
lines = content.split('\n')
print(f"\nuseJobStatusModal.ts lines 193-200 and 250-257:")
for i, line in enumerate(lines[192:201], 193):
    print(f"  L{i}: {line}")
for i, line in enumerate(lines[249:258], 250):
    print(f"  L{i}: {line}")

# ===== 12. shared-search-details-modal.tsx =====
# loadDetails function changes on render - wrap in useCallback
path = f'{base}/components/modals/shared-search-details-modal.tsx'
content = read(path)
# The current useEffect has [open, sharedSearchId, loadDetails] - we added loadDetails
# But loadDetails is defined as regular async fn, needs useCallback
old = '  const loadDetails = async () => {'
new = '  const loadDetails = useCallback(async () => {'
if old in content:
    idx_start = content.find(old)
    # Find end 
    idx_end = content.find('\n  useEffect(', idx_start + 10)
    if idx_end == -1:
        idx_end = content.find('\n  const ', idx_start + 10)
    if idx_end != -1:
        fn_body = content[idx_start:idx_end]
        new_fn = fn_body.replace('  const loadDetails = async () => {', '  const loadDetails = useCallback(async () => {')
        last_brace = new_fn.rfind('\n  }')
        if last_brace != -1:
            new_fn = new_fn[:last_brace + 4] + ', [sharedSearchId])'
        content = content[:idx_start] + new_fn + content[idx_end:]
        write(path, content)
        print(f"  FIXED loadDetails useCallback: shared-search-details-modal.tsx")
    else:
        print(f"  MISS loadDetails end: shared-search-details-modal.tsx")
else:
    if 'loadDetails = useCallback' in content:
        print(f"  loadDetails already wrapped")
    else:
        print(f"  MISS loadDetails fn: shared-search-details-modal.tsx")

# ===== 13. useChatSession.ts =====
# companyId missing at lines 324 and 401
path = f'{base}/components/pages/chat-page/chat-core/useChatSession.ts'
content = read(path)
# Both effects have [emptyFieldNotifications, setMessages] 
# Line 324 has: }, [emptyFieldNotifications, setMessages])
# Line 401 has: }, [emptyFieldNotifications, setMessages])
# Both need companyId added
# Replace both occurrences
content = content.replace(
    '  }, [emptyFieldNotifications, setMessages])',
    '  }, [emptyFieldNotifications, setMessages, companyId])'
)
write(path, content)
print(f"  FIXED companyId deps in both effects: useChatSession.ts")

# ===== 14. useChatPageHandlers.tsx =====
# addChatMessage: missing at 564, unnecessary at 619
path = f'{base}/components/pages/chat-page/useChatPageHandlers.tsx'
content = read(path)
# Add addChatMessage to handleSendMessage deps (the big one)
# And remove it from handlePipelineAction
# Handle the big deps array for handleSendMessage
content = content.replace(
    ', chatConversationId, setChatConversationId])',
    ', chatConversationId, setChatConversationId, addChatMessage])'
)
# Remove from handlePipelineAction
content = content.replace(
    ', addChatMessage])\n\n\n  const handleSmartSearchCancel',
    '])\n\n\n  const handleSmartSearchCancel'
)
write(path, content)
print(f"  FIXED handleSendMessage/handlePipelineAction addChatMessage: useChatPageHandlers.tsx")

print("\nDone with all fixes!")
