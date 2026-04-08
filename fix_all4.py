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

# ===== 1. useChatPageHandlers.tsx =====
# addChatMessage missing in handlePipelineAction deps
path = f'{base}/components/pages/chat-page/useChatPageHandlers.tsx'
fix(path,
    '  }, [messages.length, contextData, setContextData, setIsSchedulingModalOpen, setMessages, setSelectedCandidateForScheduling])',
    '  }, [messages.length, contextData, setContextData, setIsSchedulingModalOpen, setMessages, setSelectedCandidateForScheduling, addChatMessage])',
    'addChatMessage dep'
)

# ===== 2. add-to-job-modal.tsx =====
# checkDuplicates missing dep
path = f'{base}/components/modals/add-to-job-modal.tsx'
# The useEffect has [selectedJobId, candidateIds] but is missing checkDuplicates
fix(path,
    '  }, [selectedJobId, candidateIds])\n\n  const checkDuplicates',
    '  }, [selectedJobId, candidateIds, checkDuplicates])\n\n  const checkDuplicates',
    'checkDuplicates dep'
)

# ===== 3. useExpandedChatWiring.ts =====
# Multiple useCallback with missing 'state' dep  
# Warnings at lines 42, 47, 51, 62, 95, 100, 104, 115, 123, 327, 332, 336, 347
path = f'{base}/components/lia-float/useLiaChatPanelState.ts'
if not os.path.exists(path):
    path = f'{base}/components/lia-float/useLiaChatPanelState.ts'
    
print(f"\nChecking useLiaChatPanelState.ts...")
content = read(path)
lines = content.split('\n')
print(f"  Lines around 42:")
for i, line in enumerate(lines[39:55], 40):
    print(f"  L{i}: {line}")

# The file is useLiaChatPanelState.ts - line 42,47,51,62 etc are useCallback
# Let's find what's around those lines

print(f"\n  Lines around 95:")
for i, line in enumerate(lines[92:130], 93):
    print(f"  L{i}: {line}")

print("Done with inspection")
