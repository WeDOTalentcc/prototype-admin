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

def remove_toast_dep(content):
    content = re.sub(r'\[toast\]', '[]', content)
    content = re.sub(r'\[toast,\s*', '[', content)
    content = re.sub(r',\s*\btoast\b(?=\s*\])', '', content)
    content = re.sub(r'\btoast,\s*', '', content)
    return content

# ===== 1. useChatMessages.ts =====
path = f'{base}/components/pages/chat-page/chat-core/useChatMessages.ts'
content = read(path)
original = content

# Fix scrollToBottom missing dep (line 82 hook)
content = content.replace(
    '  }, [messages, chatStreamingContent, checkNewMessageIndicator])',
    '  }, [messages, chatStreamingContent, checkNewMessageIndicator, scrollToBottom])'
)

# Fix toast unnecessary deps at lines 170, 228, 232, 236
content = remove_toast_dep(content)

if content != original:
    write(path, content)
    print(f"FIXED useChatMessages.ts")
else:
    print("MISS useChatMessages.ts")

# Verify
c2 = read(path)
print(f"  scrollToBottom in deps: {', scrollToBottom]' in c2}")
print(f"  toast deps removed: {'], [toast]' not in c2 and ', toast]' not in c2}")

# ===== 2. lia-analysis-modal.tsx =====
# Line 95: toast unnecessary dep in useCallback
path = f'{base}/components/modals/lia-analysis-modal.tsx'
content = read(path)
original = content
content = remove_toast_dep(content)
if content != original:
    write(path, content)
    print("FIXED lia-analysis-modal.tsx: removed toast deps")
else:
    print("MISS lia-analysis-modal.tsx: no toast deps in arrays")

# ===== 3. useUniversalTransitionModal.tsx =====
# Line 254: missing deps
path = f'{base}/components/kanban/components/useUniversalTransitionModal.tsx'
fix(path,
    '  }, [isOpen, currentSubStatusOptions, resetInterpret, initialPrompt])',
    '  }, [isOpen, currentSubStatusOptions, resetInterpret, initialPrompt, candidates, companyId, currentActionBehavior, fromStage, jobTitle, selectedToStage, sendMessage])',
    'missing deps'
)

# ===== 4. useChatPageHandlers.tsx =====
# Toast unnecessary deps (170, 228, 232, 236) and companyId missing (324, 401), addChatMessage missing (564)
path = f'{base}/components/pages/chat-page/useChatPageHandlers.tsx'
content = read(path)
original = content

# Remove toast from deps
content = remove_toast_dep(content)

# Add companyId at line 324 (useEffect) and 401 (useCallback)
# Need to look at the actual patterns
# Line 324: useEffect with missing companyId
lines = content.split('\n')
print(f"\nuseChatPageHandlers line 318-330:")
for i, line in enumerate(lines[317:331], 318):
    print(f"  L{i}: {line}")

if content != original:
    write(path, content)
    print("FIXED useChatPageHandlers.tsx: removed toast deps")

# ===== 5. add-to-job-modal.tsx =====
# Line 28: toast dep - but the warning shows line 28 which is just imports
# ESLint says the useEffect hook starts at 28 
path = f'{base}/components/modals/add-to-job-modal.tsx'
content = read(path)
lines = content.split('\n')
print(f"\nadd-to-job-modal.tsx line 25-35:")
for i, line in enumerate(lines[24:36], 25):
    print(f"  L{i}: {line}")

# Find all ] with toast in them
matches = list(re.finditer(r'\btost\b|\btoast\b', content))
print(f"Found {len(matches)} 'toast' occurrences")
for m in matches:
    start = max(0, m.start()-20)
    print(f"  '{content[start:m.end()+30]}'")

# Actually let's check via eslint output: line 28 useEffect
# The warning said line 28 was the useEffect - let me look at context
# Search for useEffect near line 28
lines = content.split('\n')
for i, line in enumerate(lines[22:35], 23):
    print(f"  L{i}: {repr(line)}")

print("\nAll done!")
