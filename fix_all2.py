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

# ===== useJobUnpublish.ts =====
# Line 159: missing dep 'jobs' - current: [isOpen, jobs.length, candidates.length]
fix(
    f'{base}/components/modals/useJobUnpublish.ts',
    '  }, [isOpen, jobs.length, candidates.length])',
    '  }, [isOpen, jobs, candidates.length])',
    'jobs dep'
)

# ===== useJobUnpublishModal.ts =====
# Line 159: missing dep 'jobs'
fix(
    f'{base}/components/modals/useJobUnpublishModal.ts',
    '  }, [isOpen, jobs.length, candidates.length])',
    '  }, [isOpen, jobs, candidates.length])',
    'jobs dep'
)

# ===== useStageTransitionActions.ts =====
# Line 81: missing dep 'suggestedActions'
fix(
    f'{base}/components/modals/useStageTransitionActions.ts',
    '  }, [isOpen, currentStage, newStage])\n\n  const regenerateMessage',
    '  }, [isOpen, currentStage, newStage, suggestedActions])\n\n  const regenerateMessage',
    'suggestedActions dep'
)
# Line 150: missing dep 'regenerateMessage'
fix(
    f'{base}/components/modals/useStageTransitionActions.ts',
    '  }, [isOpen, selectedAction, channel])',
    '  }, [isOpen, selectedAction, channel, regenerateMessage])',
    'regenerateMessage dep'
)

# ===== useStageTransitionModal.ts =====
# Line 91: missing dep 'suggestedActions'
fix(
    f'{base}/components/modals/useStageTransitionModal.ts',
    '  }, [isOpen, currentStage, newStage])\n\n  const regenerateMessage',
    '  }, [isOpen, currentStage, newStage, suggestedActions])\n\n  const regenerateMessage',
    'suggestedActions dep'
)
# Line 155: missing dep 'regenerateMessage'
fix(
    f'{base}/components/modals/useStageTransitionModal.ts',
    '  }, [isOpen, selectedAction, channel])',
    '  }, [isOpen, selectedAction, channel, regenerateMessage])',
    'regenerateMessage dep'
)

# ===== useUniversalTransitionModal.tsx =====
# Line 254: missing deps - need to inspect
path = f'{base}/components/kanban/components/useUniversalTransitionModal.tsx'
content = read(path)
lines = content.split('\n')
print(f"\nuseUniversalTransitionModal.tsx lines 248-265:")
for i, line in enumerate(lines[247:266], 248):
    print(f"  L{i}: {line}")

# ===== lia-analysis-modal.tsx =====
# Line 137: missing dep 'salaryInfo'
path = f'{base}/components/modals/lia-analysis-modal.tsx'
content = read(path)
lines = content.split('\n')
print(f"\nlia-analysis-modal.tsx lines 130-145:")
for i, line in enumerate(lines[129:146], 130):
    print(f"  L{i}: {line}")

# ===== useChatMessages.ts - scrollToBottom missing dep =====
path = f'{base}/components/pages/chat-page/chat-core/useChatMessages.ts'
content = read(path)
lines = content.split('\n')
print(f"\nuseChatMessages.ts lines 78-90:")
for i, line in enumerate(lines[77:91], 78):
    print(f"  L{i}: {line}")

print("\nDone")
