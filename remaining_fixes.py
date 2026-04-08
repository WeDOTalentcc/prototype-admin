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

# ===== 1. useExpandedChatWiring.ts =====
# state missing in useEffect at line 291
path = f'{base}/components/expanded-chat/hooks/useExpandedChatWiring.ts'
fix(path,
    '  }, [isOpen, initialMessage, state.messages.length, state.isTypingEffect, handleSendMessage])',
    '  }, [isOpen, initialMessage, state.messages.length, state.isTypingEffect, handleSendMessage, state])',
    'state dep'
)

# ===== 2. SalaryStage.tsx =====
# salaryInfo missing in useMemo [salaryInfo.benefits]
path = f'{base}/components/expanded-chat/stages/SalaryStage.tsx'
# The useMemo accesses salaryInfo.benefits - the deps already have salaryInfo.benefits
# ESLint wants salaryInfo (the whole object) - let's just add it
fix(path,
    '  }, [salaryInfo.benefits])',
    '  }, [salaryInfo.benefits, salaryInfo])',
    'salaryInfo dep'
)

# ===== 3. useJobStatusModal.ts =====
# Line 197: missing 'jobs'
path = f'{base}/components/modals/job-status/useJobStatusModal.ts'
content = read(path)
# Current: }, [isOpen, jobs.length, candidates.length, isPauseMode])
fix(path,
    '  }, [isOpen, jobs.length, candidates.length, isPauseMode])',
    '  }, [isOpen, jobs, candidates.length, isPauseMode])',
    'jobs dep'
)

# Line 254: missing 'handleSubmitAndNavigate'  
# Current deps: [hasProposalBlock, isPauseMode, isCancelMode, candidatesInProposal.length, notifyApplicants, onNavigateToJobWithCommunication]
fix(path,
    '  }, [hasProposalBlock, isPauseMode, isCancelMode, candidatesInProposal.length, notifyApplicants, onNavigateToJobWithCommunication])',
    '  }, [hasProposalBlock, isPauseMode, isCancelMode, candidatesInProposal.length, notifyApplicants, onNavigateToJobWithCommunication, handleSubmitAndNavigate])',
    'handleSubmitAndNavigate dep'
)

# ===== Check shared-search-details-modal.tsx - useCallback import needed =====
path = f'{base}/components/modals/shared-search-details-modal.tsx'
content = read(path)
if 'useCallback' not in content:
    content = content.replace(
        "import { useState",
        "import { useState, useCallback"
    )
    write(path, content)
    print(f"  Added useCallback import: shared-search-details-modal.tsx")
else:
    print(f"  useCallback already imported: shared-search-details-modal.tsx")

# Check add-to-job-modal.tsx - useCallback import
path = f'{base}/components/modals/add-to-job-modal.tsx'
content = read(path)
if 'useCallback' not in content.split('from "react"')[0]:
    # Check how it imports
    idx = content.find('from "react"')
    if idx != -1:
        snippet = content[max(0,idx-100):idx+15]
        print(f"  add-to-job-modal react import: {repr(snippet)}")
    if 'useCallback' not in content.split('react')[0] and 'useCallback' not in content:
        content = content.replace(
            'import { useState,',
            'import { useState, useCallback,'
        )
        write(path, content)
        print(f"  Added useCallback import: add-to-job-modal.tsx")
    else:
        print(f"  useCallback already in add-to-job-modal.tsx")

# ===== voice-chat-button.tsx: Check useCallback import =====
path = f'{base}/components/chat/voice-chat-button.tsx'
content = read(path)
print(f"\nvoice-chat-button.tsx imports check:")
for line in content.split('\n')[:5]:
    print(f"  {line}")

print("\nDone!")
